# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, _
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    partial_payment_id = fields.Many2one(
        "account.payment", string="Partial Payment", copy=False, readonly=True
    )

    def _reverse_moves(self, default_values_list=None, cancel=False):
        if self._context.get("partial_exchange_move_id") and default_values_list:
            moves = (
                self.env["account.move"]
                .sudo()
                .browse(self._context.get("partial_exchange_move_id"))
            )
            for mv in moves:
                default_values_list.append(
                    {
                        "date": mv._get_accounting_date(
                            mv.date, mv._affect_tax_report()
                        ),
                        "ref": _("Reversal of: %s") % mv.name,
                    }
                )
        return super()._reverse_moves(default_values_list, cancel)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def reconcile(self):
        """
        Override reconcile method to handle partial exchange gain/loss for payments.
        """
        result = super(AccountMoveLine, self).reconcile()
        from_payment = self._context.get(
            "create_payment_from_wizard", False
        ) or self._context.get("from_payment", False)
        if (
                not from_payment
                or self._context.get("no_exchange_difference")
                or not result
        ):
            return result

        self._handle_partial_exchange_difference(result)
        return result

    def _handle_partial_exchange_difference(self, result):
        """
        Process partial exchange rate differences during reconciliation.
        """
        if result.get("full_reconcile"):
            payment_ids = result["full_reconcile"].reconciled_line_ids.mapped(
                "payment_id"
            )
            exchange = result["full_reconcile"].exchange_move_id
            reconcile_moves = result["full_reconcile"].reconciled_line_ids.mapped(
                "move_id"
            )

            # Check if it's a partial or full payment
            if len(payment_ids) < 2:
                # wizard = self.env["account.move.reversal"].with_context(active_model="account.move", active_ids=exchange.ids).create(
                #         {
                #             "date_mode": "entry"
                #         }
                #     )
                #
                # wizard.reverse_moves()
                return
        partial_recon = result["partials"]
        payment_diff_vals = self._calculate_bs_exchange_differences(partial_recon)
        current_partials, full_reconcile = self._create_bs_partial_exchange_moves(
            payment_diff_vals, partial_recon
        )

        if current_partials and not full_reconcile:
            partial_recon |= current_partials
            result["partials"] = partial_recon
        if full_reconcile:
            result["full_reconcile"] = full_reconcile

    def _calculate_bs_exchange_differences(self, partials):
        """
        Calculate the exchange rate differences for partial payments.
        """
        diff_values_per_moves = {}
        payment_diff_vals = {}
        for partial in partials:
            payment_line, invoice_line = self._get_bs_payment_and_invoice_line(partial)
            payment = payment_line.payment_id
            if (
                    not payment
                    or not invoice_line
                    or invoice_line.move_id.move_type == "entry"
                    or partial.company_currency_id == invoice_line.currency_id
            ):
                continue

            invoice_rate = self._get_bs_invoice_rate(invoice_line)
            payment_rate = self._get_bs_invoice_rate(payment_line)
            amount = min(partial.debit_amount_currency, partial.credit_amount_currency)
            invoice_amount = invoice_rate * amount
            payment_amt = payment_rate * amount
            # p_val = payment_diff_vals.get(payment, {'payment_line': payment_line, 'diff_amt': 0})
            m_val = diff_values_per_moves.get(
                invoice_line.move_id,
                {"payment_line": payment_line, "diff_amt": 0, "payment": payment},
            )
            diff_amount = m_val.get("diff_amt", 0)
            diff_amount += payment_amt - invoice_amount
            m_val["diff_amt"] = diff_amount
            m_val["payment_line"] = payment_line
            m_val["payment"] = payment
            diff_values_per_moves[invoice_line.move_id] = m_val

        return diff_values_per_moves

    def _get_bs_payment_and_invoice_line(self, partial):
        """
        Identify the payment and invoice line associated with the partial payment.
        """
        invoice_line = self.env["account.move.line"]
        payment_line = self.env["account.move.line"]

        if partial.credit_move_id.payment_id:
            payment_line = partial.credit_move_id
        elif partial.debit_move_id.payment_id:
            payment_line = partial.debit_move_id

        if not partial.credit_move_id.payment_id:
            invoice_line = partial.credit_move_id
        elif not partial.debit_move_id.payment_id:
            invoice_line = partial.debit_move_id

        return payment_line, invoice_line

    def _get_bs_invoice_rate(self, invoice_line):
        """
        Get the currency exchange rate for the invoice.
        """
        move = invoice_line.move_id
        return move.manual_currency_inverse_rate

    def _create_bs_partial_exchange_moves(self, payment_diff_vals, partial_results):
        """
        Create accounting moves for partial payment currency exchange differences.
        """

        if not payment_diff_vals or not partial_results:
            return None, None

        partial_reconciles = partial_results
        current_partials = self.env["account.partial.reconcile"]

        for move, value in payment_diff_vals.items():
            payment = value.get("payment")
            diff_amount = value.get("diff_amt", 0)
            payment_line = value.get("payment_line")

            if float_is_zero(
                    diff_amount, precision_rounding=payment.company_id.currency_id.rounding
            ):
                continue

            journal = payment.company_id.currency_exchange_journal_id
            exchange_account = self._get_bs_exchange_account(payment, diff_amount)
            partner_account = self._get_bs_partner_account(payment, diff_amount)

            exchange_move_vals = self._prepare_bs_partial_exchange_move_vals(
                payment, diff_amount, journal, exchange_account, partner_account
            )
            exchange_move_vals["ref"] = move.display_name
            exchange_move = self.env["account.move"].create(exchange_move_vals)
            exchange_move._post(soft=False)

            to_reconcile_lines = self._get_bs_to_reconcile_lines(
                move, payment, exchange_account
            )

            # Combine payment and exchange move line IDs and filter for receivable/payable accounts
            clines = (to_reconcile_lines + exchange_move.line_ids).filtered(
                lambda x: x.account_internal_type in ["receivable", "payable"]
            )

            # Sort the lines by maturity date or transaction date and then by currency
            sorted_lines = clines.sorted(
                key=lambda line: (line.date_maturity or line.date, line.currency_id)
            )
            debit_line = credit_line = self.env["account.move.line"]

            if (
                    exchange_account
                    == payment.company_id.income_currency_exchange_account_id
            ):
                credit_line = sorted_lines[0]
                debit_line = sorted_lines[1]
            else:
                credit_line = sorted_lines[1]
                debit_line = sorted_lines[0]

            if debit_line and credit_line:
                partials_vals = {
                    "amount": abs(diff_amount),
                    "debit_amount_currency": 0,
                    "credit_amount_currency": 0,
                    "debit_move_id": debit_line.id,
                    "credit_move_id": credit_line.id,
                    "partial_exchange_move_id": exchange_move.id,
                }
                partials = self.env["account.partial.reconcile"].create(partials_vals)
                partial_reconciles |= partials
                current_partials |= partials

        return current_partials, self._finalize_bs_full_reconcile(current_partials)

    def _finalize_bs_full_reconcile(self, current_partials):
        """
        Create full reconciliation if no unpaid invoices remain.
        """
        unpaid_invoices = self.move_id.filtered(
            lambda move: move.is_invoice(include_receipts=True)
                         and move.payment_state not in ("paid", "in_payment")
        )

        if not unpaid_invoices:
            involved_lines, involved_partials = self._get_bs_involved_lines_partials(
                current_partials
            )
            return self.env["account.full.reconcile"].create(
                {
                    "partial_reconcile_ids": [(6, 0, involved_partials.ids)],
                    "reconciled_line_ids": [(6, 0, involved_lines.ids)],
                }
            )

        return None

    def _get_bs_involved_lines_partials(self, current_partials):
        """
        Get the involved lines and partial reconciliations for full reconcile.
        """
        involved_lines = self.sorted(
            key=lambda line: (line.date_maturity or line.date, line.currency_id)
        )
        involved_partials = current_partials

        while involved_lines:
            current_partials = (
                                       involved_lines.matched_debit_ids + involved_lines.matched_credit_ids
                               ) - involved_partials
            involved_partials |= current_partials
            involved_lines = (
                                     current_partials.debit_move_id + current_partials.credit_move_id
                             ) - involved_lines

        return (
                involved_partials.debit_move_id + involved_partials.credit_move_id
        ), involved_partials

    def _get_bs_exchange_account(self, payment, diff_amount):
        """
        Get the exchange gain or loss account based on the difference amount.
        """
        company = payment.company_id
        if payment.partner_type == "supplier":
            return (
                company.expense_currency_exchange_account_id
                if diff_amount > 0
                else company.income_currency_exchange_account_id
            )
        elif payment.partner_type == "customer":
            return (
                company.income_currency_exchange_account_id
                if diff_amount > 0
                else company.expense_currency_exchange_account_id
            )

    def _get_bs_to_reconcile_lines(self, move, payment, exchange_account):
        """
        Get the exchange gain or loss account based on the difference amount.
        """
        company = payment.company_id
        if payment.partner_type == "supplier":
            return (
                payment.line_ids
                if exchange_account != company.income_currency_exchange_account_id
                else self.filtered(
                    lambda x: x not in payment.line_ids and x.move_id == move
                )
            )
        elif payment.partner_type == "customer":
            return (
                payment.line_ids
                if exchange_account == company.income_currency_exchange_account_id
                else self.filtered(
                    lambda x: x not in payment.line_ids and x.move_id == move
                )
            )

    def _get_bs_partner_account(self, payment, diff_amount):
        """
        Get the partner account (receivable or payable) based on the difference amount.
        """
        partner = payment.partner_id
        if payment.partner_type == "supplier":
            return partner.property_account_payable_id
            # return partner.property_account_payable_id if diff_amount > 0 else partner.property_account_receivable_id
        elif payment.partner_type == "customer":
            return partner.property_account_receivable_id
            # return partner.property_account_receivable_id if diff_amount > 0 else partner.property_account_payable_id

    def _prepare_bs_partial_exchange_move_vals(
            self, payment, diff_amount, journal, exchange_account, partner_account
    ):
        """
        Prepare the values for creating the exchange rate difference move.

        """
        if payment.partner_type == "supplier":
            diff_amount = diff_amount * (-1)
        return {
            "move_type": "entry",
            "date": payment.date,
            "journal_id": journal.id,
            "ref": payment.ref,
            "partial_payment_id": payment.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "name": _("Partial payment currency exchange rate difference"),
                        "credit": -diff_amount if diff_amount < 0.0 else 0.0,
                        "debit": diff_amount if diff_amount > 0.0 else 0.0,
                        "amount_currency": 0,
                        "account_id": partner_account.id,
                        "currency_id": payment.company_id.currency_id.id,
                        "partner_id": payment.partner_id.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "name": _("Partial payment currency exchange rate difference"),
                        "credit": diff_amount if diff_amount > 0.0 else 0.0,
                        "debit": -diff_amount if diff_amount < 0.0 else 0.0,
                        "amount_currency": 0,
                        "account_id": exchange_account.id,
                        "currency_id": payment.company_id.currency_id.id,
                        "partner_id": payment.partner_id.id,
                    },
                ),
            ],
        }
