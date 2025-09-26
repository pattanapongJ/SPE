from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def write(self, vals):
        res = super().write(vals)
        if 'tax_base_amount' in vals and self.tax_line_id and self.tax_exigible:
            if len(self.tax_invoice_ids)>1:
                # removed the last line if they split tax
                self.tax_invoice_ids[-1].unlink()
            for tax_line in self.tax_invoice_ids:
                sign = self.move_id.move_type in ['out_refund', 'in_refund'] and -1 or 1
                tax_line.write({"tax_base_amount": sign * abs(self.tax_base_amount),
                                "balance": sign * abs(self.balance)})

        return res