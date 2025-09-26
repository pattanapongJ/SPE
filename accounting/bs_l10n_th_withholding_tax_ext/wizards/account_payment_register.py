from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _update_payment_register(self, amount_wt, inv_lines):
        rounded_value = self.currency_id.round(amount_wt)
        return super(AccountPaymentRegister, self)._update_payment_register(rounded_value, inv_lines)

    @api.onchange("payment_difference_handling")
    def _onchange_payment_difference_handling(self):
        if not self.payment_difference_handling == "reconcile_multi_deduct":
            return
        if self._context.get("active_model") == "account.move":
            active_ids = self._context.get("active_ids", [])
            invoices = self.env["account.move"].browse(active_ids)
            inv_lines = invoices.mapped("invoice_line_ids").filtered("wt_tax_id")
            if inv_lines:
                # Case WHT only, ensure only 1 wizard
                self.ensure_one()
                deductions = [(5, 0, 0)]
                for line in inv_lines:
                    base_amount = line._get_wt_base_amount(
                        self.currency_id, self.payment_date
                    )
                    deduct = {
                        "wt_tax_id": line.wt_tax_id.id,
                        "account_id": line.wt_tax_id.account_id.id,
                        "name": line.wt_tax_id.display_name,
                        "amount": self.currency_id.round(line.wt_tax_id.amount / 100 * base_amount),
                    }
                    deductions.append((0, 0, deduct))
                self.deduction_ids = deductions
