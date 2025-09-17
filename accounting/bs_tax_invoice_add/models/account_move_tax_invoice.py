from odoo import api, fields, models


class AccountMoveTaxInvoice(models.Model):
    _inherit = 'account.move.tax.invoice'

    @api.model
    def create(self, vals):
        tax_invoice = super().create(vals)
        for line in tax_invoice.filtered(lambda x: x.move_id and x.move_id.reversed_entry_id):
            sign = tax_invoice.move_id.move_type in ['out_refund', 'in_refund'] and -1 or 1
            line.update({
                'tax_base_amount': sign * abs(line.tax_base_amount),
                'balance': sign * abs(line.balance),
            })
        return tax_invoice
