import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'
    
    def _prepare_stock_return_picking_line_vals_from_move(self, stock_move, moves=None):
        res = super()._prepare_stock_return_picking_line_vals_from_move(stock_move, moves)
        if stock_move.sale_order_line_b_c_r:
            if isinstance(res, list):
                for line in res:
                    line['quantity'] -= stock_move.sale_order_line_b_c_r.product_uom_qty
            elif isinstance(res, dict):
                res['quantity'] -= stock_move.sale_order_line_b_c_r.product_uom_qty

        return res