from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, values):
        res = super(AccountMove, self).create(values)
        if 'invoice_line_ids' in values and len(values.get('invoice_line_ids','')) != len(res.invoice_line_ids):
            for inv_val in values.get('invoice_line_ids'):
                inv_val[1] = 0

            res.update({
                'invoice_line_ids': values.get('invoice_line_ids')
            })
        return res
