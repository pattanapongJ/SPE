from odoo import api, fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder)
        for move in res.filtered(lambda move: move.account_move_ids or move.stock_valuation_layer_ids):
            move.stock_valuation_layer_ids.write(
                {
                    'finance_dimension_4_id': move.finance_dimension_4_id.id,
                    'finance_dimension_5_id': move.finance_dimension_5_id.id,
                    'finance_dimension_6_id': move.finance_dimension_6_id.id,
                    'finance_dimension_7_id': move.finance_dimension_7_id.id,
                    'finance_dimension_8_id': move.finance_dimension_8_id.id,
                    'finance_dimension_9_id': move.finance_dimension_9_id.id,
                    'finance_dimension_10_id': move.finance_dimension_10_id.id
                }
            )

            if not move.account_move_ids:
                continue

            if move.picking_id:
                move.account_move_ids.write({
                    'finance_dimension_4_id': move.picking_id.finance_dimension_4_id.id,
                    'finance_dimension_5_id': move.picking_id.finance_dimension_5_id.id,
                    'finance_dimension_6_id': move.picking_id.finance_dimension_6_id.id,
                    'finance_dimension_7_id': move.picking_id.finance_dimension_7_id.id,
                    'finance_dimension_8_id': move.picking_id.finance_dimension_8_id.id,
                    'finance_dimension_9_id': move.picking_id.finance_dimension_9_id.id,
                    'finance_dimension_10_id': move.picking_id.finance_dimension_10_id.id  
                })

            move.account_move_ids.line_ids.write(
                {
                    'finance_dimension_4_id': move.finance_dimension_4_id.id,
                    'finance_dimension_5_id': move.finance_dimension_5_id.id,
                    'finance_dimension_6_id': move.finance_dimension_6_id.id,
                    'finance_dimension_7_id': move.finance_dimension_7_id.id,
                    'finance_dimension_8_id': move.finance_dimension_8_id.id,
                    'finance_dimension_9_id': move.finance_dimension_9_id.id,
                    'finance_dimension_10_id': move.finance_dimension_10_id.id   
                }
            )

        return res

    @api.model
    def default_get(self, fields):
        rec = super().default_get(fields)
        if self.picking_id:
            self.update({
                'finance_dimension_4_id': self.finance_dimension_4_id or self.picking_id.finance_dimension_4_id.id,
                'finance_dimension_5_id': self.finance_dimension_5_id or self.picking_id.finance_dimension_5_id.id,
                'finance_dimension_6_id': self.finance_dimension_6_id or self.picking_id.finance_dimension_6_id.id,
                'finance_dimension_7_id': self.finance_dimension_7_id or self.picking_id.finance_dimension_7_id.id,
                'finance_dimension_8_id': self.finance_dimension_8_id or self.picking_id.finance_dimension_8_id.id,
                'finance_dimension_9_id': self.finance_dimension_9_id or self.picking_id.finance_dimension_9_id.id,
                'finance_dimension_10_id': self.finance_dimension_10_id or self.picking_id.finance_dimension_10_id.id
            })

        return rec
