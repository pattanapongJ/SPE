from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super().action_post()
        for move in self:
            lines = move.invoice_line_ids | move.line_ids
            for line in lines.filtered(lambda x: x.asset_id):
                line.asset_id.write({
                    'finance_dimension_4_id': line.finance_dimension_4_id.id,
                    'finance_dimension_5_id': line.finance_dimension_5_id.id,
                    'finance_dimension_6_id': line.finance_dimension_6_id.id,
                    'finance_dimension_7_id': line.finance_dimension_7_id.id,
                    'finance_dimension_8_id': line.finance_dimension_8_id.id,
                    'finance_dimension_9_id': line.finance_dimension_9_id.id,
                    'finance_dimension_10_id': line.finance_dimension_10_id.id
                })
        return  res