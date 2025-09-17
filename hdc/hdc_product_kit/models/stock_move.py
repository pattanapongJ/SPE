# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero, OrderedSet

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _compute_manufactured_quantities(self, product_id, manufacturing_qty, manufacturing_bom, filters):
        qty_ratios = []
        boms, bom_sub_lines = manufacturing_bom.explode(product_id, manufacturing_qty)
        for bom_line, bom_line_data in bom_sub_lines:
            # Skip service products since we do not manufacture or deliver them
            if bom_line.product_id.type == 'service':
                continue
            # Check if the required quantity for this component is zero to avoid division by zero
            if float_is_zero(bom_line_data['qty'], precision_rounding=bom_line.product_uom_id.rounding):
                continue
            bom_line_moves = self.filtered(lambda m: m.bom_line_id == bom_line or m.product_id == bom_line.product_id)
            if bom_line_moves:
                uom_qty_per_product = bom_line_data['qty'] / bom_line_data['original_qty']
                qty_per_product = bom_line.product_uom_id._compute_quantity(uom_qty_per_product, bom_line.product_id.uom_id, round=False)
                if not qty_per_product:
                    continue
                incoming_moves = bom_line_moves.filtered(filters['incoming_moves'])
                outgoing_moves = bom_line_moves.filtered(filters['outgoing_moves'])
                qty_processed = sum(incoming_moves.mapped('product_qty')) - sum(outgoing_moves.mapped('product_qty'))
                qty_ratios.append(float_round(qty_processed / qty_per_product, precision_rounding=bom_line.product_id.uom_id.rounding))
            else:
                return 0.0

        if qty_ratios:
            return min(qty_ratios) // 1
        else:
            return 0.0

    