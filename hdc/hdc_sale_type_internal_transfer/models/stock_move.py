# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class StockMoveInheritAddon(models.Model):
    _inherit = "stock.move"

    sale_order_line_b_c_r = fields.Many2one("sale.order.line", string = "Sale Order Line BCR")

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        self.ensure_one()
        res = super()._prepare_move_line_vals(quantity, reserved_quant)
        if self.picking_id.picking_type_id.code == 'internal':
            location_dest_id = self.picking_id.location_dest_id
            res.update({"location_dest_id": location_dest_id.id})
        return res
    
    def _prepare_move_line_vals_b_c_urgen(self,qty_done,location_dest_id,lot_id):
        vals = {
            'move_id': self.id,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'location_id': self.location_id.id,
            'location_dest_id': location_dest_id,
            'picking_id': self.picking_id.id,
            'company_id': self.company_id.id,
            'qty_done':qty_done,
            'lot_id': lot_id,
        }
        return vals
        
    def create_move_line_b_c_urgen(self):
        deliveries = self.env['stock.picking'].search([
                ('b_c_urgent_delivery_id', '=', self.picking_id.b_c_urgent_delivery_id.id),
                ('state', '=', 'done')
            ])
        move_line_ids = self.env['stock.move.line'].search([
                ('picking_id', '=', deliveries.id),
                ('product_id', '=', self.product_id.id)
            ])
        
        dict_location_qty = {}
        location_list = []
        for location_id in self.urgent_location_ids:
            if self.picking_id.b_c_urgent_delivery_id:
                for so_list in self.picking_id.b_c_urgent_delivery_id.sale_order_ids:
                    so_line_data = self.env['sale.order.line'].search([('order_id','=',so_list.id),('product_id','=',self.product_id.id),('order_id.location_id','=',location_id.id)])
                    if so_line_data:
                        for line in so_line_data:
                            if so_list.location_id.id in dict_location_qty:
                                dict_location_qty[so_list.location_id.id] += line.product_uom_qty
                            else:
                                dict_location_qty[so_list.location_id.id] = line.product_uom_qty
                                location_list.append(so_list.location_id.id)
    
        location_dest_id = self.location_dest_id._get_putaway_strategy(self.product_id).id or self.location_dest_id.id
        qty_done = self.product_uom_qty - self.urgent_pick
        if location_dest_id in dict_location_qty:
            dict_location_qty[location_dest_id] += qty_done
        else:
            dict_location_qty[location_dest_id] = qty_done
            location_list.append(location_dest_id)

        num_move_line = -1
        move_line_qty_done = 0
        qty_location = 0 
        dict_index = -1
        while num_move_line < len(move_line_ids):
            if move_line_qty_done == 0:
                num_move_line += 1
                if num_move_line < len(move_line_ids):
                    move_line_qty_done = move_line_ids[num_move_line].qty_done
                    lot_id = move_line_ids[num_move_line].lot_id
            if qty_location == 0:
                dict_index += 1
                if dict_index < len(location_list):
                    location_id = location_list[dict_index]
                    qty_location = dict_location_qty[location_id]
            if qty_location >= move_line_qty_done:
                qty_done = move_line_qty_done
            else:
                qty_done = qty_location
            move_line_qty_done -= qty_done
            qty_location -= qty_done
            if num_move_line < len(move_line_ids) and dict_index < len(location_list):
                move_line = self.env['stock.move.line'].create(self._prepare_move_line_vals_b_c_urgen(qty_done,location_id,lot_id.id))
                self.write({'move_line_ids': [(4, move_line.id)]})