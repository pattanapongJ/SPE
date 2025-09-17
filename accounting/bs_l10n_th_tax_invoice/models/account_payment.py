from odoo import api, fields, models, _


class AccountPayment(models.Model):
    _inherit = "account.payment"

    tax_journal_entry_ids = fields.Many2many(
        "account.move", string="Tax Journal Entry", compute="_compute_tax_journal_entry"
    )
    tax_journal_entry_count = fields.Integer(
        string="Tax Journal Entry Count", compute="_compute_tax_journal_entry"
    )

    @api.depends("tax_invoice_ids")
    def _compute_tax_journal_entry(self):
        for payment in self:
            _move_ids = (
                payment.tax_invoice_ids.mapped("move_id")
                if payment.tax_invoice_ids
                else []
            )
            payment.tax_journal_entry_ids = _move_ids
            payment.tax_journal_entry_count = len(_move_ids)

    def button_open_tax_journal_entries(self):
        self.ensure_one()
        action = {
            "name": _("Tax Invoice Journal Entries"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "context": {"create": False},
        }
        if len(self.tax_journal_entry_ids) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": self.tax_journal_entry_ids.id,
                }
            )
        else:
            action.update(
                {
                    "view_mode": "list,form",
                    "domain": [("id", "in", self.tax_journal_entry_ids.ids)],
                }
            )
        return action

    def button_journal_entries(self):
        action = super(AccountPayment, self).button_journal_entries()
        bill_invoice_ids = self.reconciled_invoice_ids | self.reconciled_bill_ids
        move_ids = self.move_id | self.tax_journal_entry_ids
        line_ids = self.move_id.line_ids._reconciled_lines()
        move_lines = self.env["account.move.line"].browse(line_ids)
        if move_lines.exists():
            related_moves = move_lines.mapped("move_id") - bill_invoice_ids
            move_ids |= related_moves

        return {
            "name": _("Journal Entries"),
            "view_mode": "tree,form",
            "res_model": "account.move",
            "view_id": False,
            "context": {"create": False},
            "type": "ir.actions.act_window",
            "domain": [("id", "in", move_ids.ids)],
        }

    def action_draft(self):
        for payment in self:
            payment.write({"to_clear_tax": False})
            moves = payment.tax_invoice_ids.mapped("move_id")
            for move in moves.filtered(lambda l: l.state == "draft"):
                move.ensure_one()
                move.with_context(draft_payment_include_tax_invoice=True).action_post()
        super().action_draft()


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _create_payments(self):
        payment = super(AccountPaymentRegister, self)._create_payments()
        for move in payment.tax_journal_entry_ids:
            # Remove Cost of Revenue lines . Allow to make only tax lines
            if len(move.line_ids) > 2:
                # tax_id_line_account = move.line_ids.filtered("tax_ids").mapped(
                #     "account_id"
                # )
                # remove_accounts = (
                #     self.env.ref("account.data_account_type_revenue")
                #     | self.env.ref("account.data_account_type_other_income")
                #     | self.env.ref("account.data_account_type_expenses")
                # )
                # to_remove_lines = move.line_ids.filtered(
                #     lambda x: x.account_id.id in tax_id_line_account.ids
                #     or x.account_id.user_type_id in remove_accounts
                #     or x.account_id.is_tax_account
                # )
                to_remove_lines = move.line_ids.filtered(
                    lambda x: not x.account_id.is_tax_account
                )
                to_remove_lines.with_context(force_delete=True).unlink()
        return payment
