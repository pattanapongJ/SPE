# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    deposit_exchange_difference_move_id = fields.Many2one(
        "account.move",
        string="Deposit Exchange Difference Entry",
        help="Journal entry recording the exchange difference for the deposit payment.",
        copy=False,
    )

    deposit_journal_entries_count = fields.Integer(
        string="Deposit Journal Entries Count",
        compute="_calculate_deposit_journal_entries",
    )

    deposit_journal_entries = fields.One2many(
        "account.move", "deposit_exchange_difference_move_id"
    )

    @api.depends("deposit_journal_entries")
    def _calculate_deposit_journal_entries(self):
        for move in self:
            move.deposit_journal_entries_count = len(move.deposit_journal_entries)

    def button_draft(self):
        res = super().button_draft()
        # for move in self.filtered(lambda x: x.deposit_exchange_difference_move_id):
        #     move.deposit_exchange_difference_move_id.button_draft()
        #     move.deposit_exchange_difference_move_id.button_cancel()
        return res

    def open_deposit_journal_entries(self):
        self.ensure_one()
        account_move_ids = self.deposit_journal_entries
        action = (
            self.env["ir.actions.actions"]._for_xml_id(
                "account.action_move_out_invoice_type"
            )
            if account_move_ids[0].move_type == "out_invoice"
            else self.env["ir.actions.act_window"]._for_xml_id(
                "account.action_move_in_invoice_type"
            )
        )
        if len(account_move_ids) > 1:
            action["domain"] = [("id", "in", account_move_ids.ids)]
        elif len(account_move_ids) == 1:
            form_view = [(self.env.ref("account.view_move_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = account_move_ids.id
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action

    def action_post(self):
        result = super().action_post()
        for move in self.filtered(
                lambda move: move.move_type in ["in_invoice", "out_invoice"]
        ):
            if move._is_downpayment_invoice():
                continue
            move._reconcile_deposit_exchange_difference()
        return result

    def _reconcile_deposit_exchange_difference(self):
        """Automatically reconcile the downpayment, final invoice"""
        # Initialize empty recordset for lines to reconcile
        lines_to_reconcile = self.env["account.move.line"]

        # Get and process regular downpayment order lines
        deposit_order_lines = self._get_deposit_order_lines()
        active_deposit_invoice_lines = deposit_order_lines.invoice_lines.filtered(
            lambda x: x.parent_state == "posted" and not x.reconciled
        )
        lines_to_reconcile |= active_deposit_invoice_lines

        # Process back-to-back downpayment lines
        active_bs_downpayment_lines = self.invoice_line_ids.filtered(
            lambda x: x.bs_downpayment_line_id
                      and x.parent_state == "posted"
                      and not x.reconciled
        )
        if active_bs_downpayment_lines:
            # Get related downpayment records and their invoice lines
            related_downpayment_records = active_bs_downpayment_lines.mapped(
                "bs_downpayment_line_id.downpayment_id"
            )
            related_downpayment_invoice_lines = (
                related_downpayment_records.move_ids.invoice_line_ids.filtered(
                    lambda x: x.product_id.id
                              in related_downpayment_records.product_id.ids
                              and x.parent_state == "posted"
                              and not x.reconciled
                )
            )
            # Combine back-to-back lines with their corresponding invoice lines
            if related_downpayment_invoice_lines:
                all_bs_related_lines = (
                        active_bs_downpayment_lines + related_downpayment_invoice_lines
                )
                lines_to_reconcile |= all_bs_related_lines

        # Perform manual reconciliation
        if lines_to_reconcile and len(lines_to_reconcile) >= 1:
            lines_to_reconcile.with_context(deposit_line_gain_loss=True).reconcile()

    def _get_deposit_order_lines(self):
        if self.move_type == "out_invoice":
            order_lines = self.invoice_line_ids.mapped("sale_line_ids")
            downpayment_order_lines = order_lines.filtered(
                lambda line: line.is_downpayment
            )
            return downpayment_order_lines
        else:
            order_lines = self.invoice_line_ids.mapped("purchase_line_id")
            deposit_order_lines = order_lines.filtered(lambda line: line.is_deposit)
            return deposit_order_lines

    def _is_downpayment_invoice(self):
        self.ensure_one()

        # Check for purchase order downpayment lines (for vendor bills)
        downpayment_invoice_lines = self.invoice_line_ids.filtered(
            lambda line: line.purchase_line_id.is_deposit and line.price_subtotal > 0
        )
        if len(downpayment_invoice_lines) > 0:
            return True

        # Check for sale order downpayment lines (for customer invoices)
        downpayment_invoice_lines = self.invoice_line_ids.filtered(
            lambda line: line.sale_line_ids.is_downpayment and line.price_subtotal > 0
        )
        if len(downpayment_invoice_lines) > 0:
            return True
        if self.bs_downpayment_id:
            return True
        return False


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _create_exchange_difference_move(self):
        exchange_move = super()._create_exchange_difference_move()

        if exchange_move and self._context.get("deposit_line_gain_loss"):
            self.move_id.filtered(
                lambda x: not x.deposit_exchange_difference_move_id
                          and not x._is_downpayment_invoice()
            ).write({"deposit_exchange_difference_move_id": exchange_move.id})

        return exchange_move

    def _reconciled_lines(self):
        ids = super()._reconciled_lines()
        for move in self.move_id:
            if len(move.deposit_journal_entries) > 0:
                ids.extend(self.mapped("full_reconcile_id").reconciled_line_ids.ids)

        return ids

    def reconcile(self):
        """Override to handle deposit exchange gain/loss for partial reconciliations"""
        # If not in deposit context, use standard behavior
        if not self._context.get("deposit_line_gain_loss"):
            return super(AccountMoveLine, self).reconcile()
        # Perform standard reconciliation first
        result = super(AccountMoveLine, self).reconcile()

        if not result:
            return result

        # Handle partial reconciliation for deposit exchange gain/loss
        if result.get("partials") and not result.get("full_reconcile"):
            partials = result["partials"]

            # Group partials by currency pair for processing
            partials_by_currency = {}
            for partial in partials:
                debit_currency = partial.debit_move_id.currency_id
                credit_currency = partial.credit_move_id.currency_id
                currency_key = (debit_currency.id, credit_currency.id)

                if currency_key not in partials_by_currency:
                    partials_by_currency[currency_key] = []
                partials_by_currency[currency_key].append(partial)

            # Process each currency group
            for currency_key, partial_group in partials_by_currency.items():
                self._create_partial_exchange_difference(partial_group, result)

        return result

    def _create_partial_exchange_difference(self, partials, reconcile_result):
        """Create exchange difference entries for partial reconciliation"""

        for partial in partials:
            involved_lines = partial.debit_move_id | partial.credit_move_id

            # Check if this involves deposit lines
            deposit_lines = involved_lines.filtered(
                lambda x: x.move_id._is_downpayment_invoice()
            )
            invoice_lines = involved_lines - deposit_lines

            if not (deposit_lines and invoice_lines):
                continue

            # Calculate exchange difference
            exchange_diff_data = self._calculate_deposit_exchange_difference(
                partial, deposit_lines, invoice_lines
            )

            if not exchange_diff_data:
                continue

            company = involved_lines.mapped("company_id")[0]
            different_amount = exchange_diff_data.get("amount", 0)

            if company.currency_id.is_zero(different_amount):
                continue

            # Create exchange difference move
            self._create_exchange_move_for_partial(
                partial, different_amount, involved_lines, reconcile_result
            )

    def _calculate_deposit_exchange_difference(
            self, partial, deposit_line, invoice_line
    ):
        """Calculate the exchange difference for a deposit partial reconciliation"""
        company = partial.company_id
        company_currency = company.currency_id

        # Get exchange rates
        deposit_rate = self._get_exchange_rate(deposit_line)
        invoice_rate = self._get_exchange_rate(invoice_line)

        if company_currency.compare_amounts(deposit_rate, invoice_rate) == 0:
            return None

        partial_amount = min(
            partial.debit_amount_currency, partial.credit_amount_currency
        )
        deposit_amount_currency = partial_amount * deposit_rate
        invoice_amount_currency = partial_amount * invoice_rate

        exchange_diff = invoice_amount_currency - deposit_amount_currency

        return {
            "amount": exchange_diff,
            "deposit_rate": deposit_rate,
            "invoice_rate": invoice_rate,
        }

    def _create_exchange_move_for_partial(
            self, partial, different_amount, involved_lines, reconcile_result
    ):
        """Create the actual exchange difference move for partial reconciliation"""

        company = involved_lines.mapped("company_id")[0]
        journal = company.currency_exchange_journal_id
        invoice_move = involved_lines.filtered(
            lambda x: not x.move_id._is_downpayment_invoice()
        ).mapped("move_id")[0]

        # Check journal configuration
        if not journal:
            raise UserError(
                _(
                    "You should configure the 'Exchange Gain or Loss Journal' in your company settings, to manage automatically the booking of accounting entries related to differences between exchange rates."
                )
            )
        if not journal.company_id.expense_currency_exchange_account_id:
            raise UserError(
                _(
                    "You should configure the 'Loss Exchange Rate Account' in your company settings, to manage automatically the booking of accounting entries related to differences between exchange rates."
                )
            )
        if not journal.company_id.income_currency_exchange_account_id.id:
            raise UserError(
                _(
                    "You should configure the 'Gain Exchange Rate Account' in your company settings, to manage automatically the booking of accounting entries related to differences between exchange rates."
                )
            )

        invoice_line = involved_lines.filtered(lambda l: l.move_id == invoice_move)

        # Create exchange difference lines for each involved line following Odoo standard
        exchange_move_vals = {
            "move_type": "entry",
            "date": max(line.date for line in involved_lines),
            "journal_id": journal.id,
            "ref": _("Exchange difference on deposit: %s") % invoice_move.display_name,
            "line_ids": [],
        }

        to_reconcile = []
        sequence = 0

        for line in involved_lines:
            if not company.currency_id.is_zero(line.amount_residual):
                # amount_residual_currency == 0 and amount_residual has to be fixed
                if line.amount_residual > 0.0:
                    exchange_line_account = (
                        journal.company_id.expense_currency_exchange_account_id
                    )
                else:
                    exchange_line_account = (
                        journal.company_id.income_currency_exchange_account_id
                    )

            elif line.currency_id and not line.currency_id.is_zero(
                    line.amount_residual_currency
            ):
                # amount_residual == 0 and amount_residual_currency has to be fixed
                if line.amount_residual_currency > 0.0:
                    exchange_line_account = (
                        journal.company_id.expense_currency_exchange_account_id
                    )
                else:
                    exchange_line_account = (
                        journal.company_id.income_currency_exchange_account_id
                    )
            else:
                continue

            # Create the exchange difference line pair following Odoo standard

            exchange_move_vals["line_ids"] += [
                (
                    0,
                    0,
                    {
                        "name": _("Currency exchange rate difference"),
                        "debit": (-different_amount if different_amount < 0.0 else 0.0),
                        "credit": (different_amount if different_amount > 0.0 else 0.0),
                        "amount_currency": 0,
                        "account_id": line.account_id.id,
                        "currency_id": line.currency_id.id,
                        "partner_id": line.partner_id.id,
                        "sequence": sequence,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "name": _("Currency exchange rate difference"),
                        "debit": (different_amount if different_amount > 0.0 else 0.0),
                        "credit": (
                            -different_amount if different_amount < 0.0 else 0.0
                        ),
                        "amount_currency": 0,
                        "account_id": exchange_line_account.id,
                        "currency_id": line.currency_id.id,
                        "partner_id": line.partner_id.id,
                        "sequence": sequence + 1,
                    },
                ),
            ]

            to_reconcile.append((line, sequence))
            sequence += 2

        if not exchange_move_vals["line_ids"]:
            return

        exchange_move = self.env["account.move"].create(exchange_move_vals)
        exchange_move.line_ids.write({"tax_exigible": True})

        # Link to invoice move
        invoice_move.write({"deposit_exchange_difference_move_id": exchange_move.id})

        # Reconcile lines to the newly created exchange difference journal entry
        invoice_line = involved_lines.filtered(lambda l: l.move_id == invoice_move)

        partials_vals_list = []
        for source_line, line_sequence in to_reconcile:
            exchange_diff_line = exchange_move.line_ids[line_sequence]

            if source_line.company_currency_id.is_zero(source_line.amount_residual):
                exchange_field = "amount_residual_currency"
            else:
                exchange_field = "amount_residual"

            if exchange_diff_line[exchange_field] > 0.0:
                debit_line = exchange_diff_line
                credit_line = source_line
            else:
                debit_line = source_line
                credit_line = exchange_diff_line

            partials_vals_list.append(
                {
                    "amount": abs(different_amount),
                    "debit_amount_currency": 0,
                    "credit_amount_currency": 0,
                    "debit_move_id": debit_line.id,
                    "credit_move_id": credit_line.id,
                }
            )

        if partials_vals_list:
            new_partials = self.env["account.partial.reconcile"].create(
                partials_vals_list
            )

        if exchange_move:
            accounts = involved_lines.mapped("account_id")
            exchange_move_lines = exchange_move.line_ids.filtered(
                lambda line: line.account_id == accounts[0]
            )
            involved_lines += exchange_move_lines

            exchange_diff_partials = (
                    exchange_move_lines.matched_debit_ids
                    + exchange_move_lines.matched_credit_ids
            )

            reconcile_result["partials"] |= exchange_diff_partials
            exchange_move._post(soft=False)

        # reconcile_result["full_reconcile"] = self.env["account.full.reconcile"].create(
        #     {
        #         "exchange_move_id": exchange_move and exchange_move.id,
        #         "partial_reconcile_ids": [(6, 0, reconcile_result["partials"].ids)],
        #         "reconciled_line_ids": [(6, 0, involved_lines.ids)],
        #     }
        # )

    def _get_exchange_rate(self, move_lines):
        move = move_lines.move_id
        if move.manual_currency_rate_active and move.manual_currency_inverse_rate:
            return move.manual_currency_inverse_rate
        else:
            return move.currency_id._get_conversion_rate(
                move.currency_id,
                move.company_currency_id,
                move.company_id or self.env.company,
                move.date or fields.Date.today(),
            )
