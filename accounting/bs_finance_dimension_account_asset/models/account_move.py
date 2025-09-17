from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super().action_post()
        for move in self:
            lines = move.invoice_line_ids | move.line_ids
            for line in lines.filtered(lambda x: x.asset_id):
                line.asset_id.write({
                    'finance_dimension_1_id': line.finance_dimension_1_id.id,
                    'finance_dimension_2_id': line.finance_dimension_2_id.id,
                    'finance_dimension_3_id': line.finance_dimension_3_id.id
                })
        return  res

