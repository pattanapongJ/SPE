from odoo import api, fields, models


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'bs.base.finance.dimension']


class StockMove(models.Model):
    _name = 'stock.move'
    _inherit = ['stock.move', 'bs.base.finance.dimension']

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder)
        for move in res.filtered(lambda move: move.account_move_ids or move.stock_valuation_layer_ids):
            move.stock_valuation_layer_ids.write(
                {
                    'finance_dimension_1_id': move.finance_dimension_1_id.id,
                    'finance_dimension_2_id': move.finance_dimension_2_id.id,
                    'finance_dimension_3_id': move.finance_dimension_3_id.id
                }
            )

            if not move.account_move_ids:
                continue

            if move.picking_id:
                move.account_move_ids.write({
                    'finance_dimension_1_id': move.picking_id.finance_dimension_1_id.id,
                    'finance_dimension_2_id': move.picking_id.finance_dimension_2_id.id,
                    'finance_dimension_3_id': move.picking_id.finance_dimension_3_id.id
                })

            move.account_move_ids.line_ids.write(
                {
                    'finance_dimension_1_id': move.finance_dimension_1_id.id,
                    'finance_dimension_2_id': move.finance_dimension_2_id.id,
                    'finance_dimension_3_id': move.finance_dimension_3_id.id
                }
            )

        return res

    @api.model
    def default_get(self, fields):
        rec = super().default_get(fields)
        if self.picking_id:
            self.update({
                'finance_dimension_1_id': self.finance_dimension_1_id or self.picking_id.finance_dimension_1_id.id,
                'finance_dimension_2_id': self.finance_dimension_2_id or self.picking_id.finance_dimension_2_id.id,
                'finance_dimension_3_id': self.finance_dimension_3_id or self.picking_id.finance_dimension_3_id.id
            })

        return rec


class StockValuationLayer(models.Model):
    _name = 'stock.valuation.layer'
    _inherit = ['stock.valuation.layer', 'bs.base.finance.dimension']
