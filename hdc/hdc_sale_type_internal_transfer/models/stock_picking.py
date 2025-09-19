# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools.float_utils import float_is_zero
from itertools import groupby

class Picking(models.Model):
    _inherit = "stock.picking"

    is_booth_type_id = fields.Boolean(related='order_id.type_id.is_booth',string='Is Booth Sales Types')
    b_c_urgent_delivery_id = fields.Many2one('booth.consign.urgent.delivery', string = 'Booth Consignment Urgent Delivery Transfer', tracking = True,copy=False)
    is_b_c_urgent = fields.Boolean('Booth Consignment Urgent', compute='_compute_is_b_c_urgent')
    urgent_hide_field = fields.Boolean('Urgent Hide Field', compute='_compute_urgent_hide_field')
    
    @api.depends('state')
    def _compute_is_b_c_urgent(self):
        for res in self:
            is_b_c_urgent = False
            if res.b_c_urgent_delivery_id:
                is_b_c_urgent = True
    
            res.update({"is_b_c_urgent": is_b_c_urgent})

    @api.depends('urgent_delivery_id', 'b_c_urgent_delivery_id')
    def _compute_urgent_hide_field(self):
        for rec in self:
            rec.urgent_hide_field = not (rec.urgent_delivery_id or rec.b_c_urgent_delivery_id)

    def delivery_out_done_to_in_done(self):
        for inter in self:
            if inter.picking_type_id.code == 'outgoing':
                picking_ids_in = False
                if inter.urgent_delivery_id:
                    picking_ids_in = self.env['stock.picking'].search([('urgent_delivery_id', '=', inter.urgent_delivery_id.id),('state', 'not in', ['done','cancel']),('picking_type_id.code','=','incoming')])
                elif inter.b_c_urgent_delivery_id:
                    picking_ids_in = self.env['stock.picking'].search([('b_c_urgent_delivery_id', '=', inter.b_c_urgent_delivery_id.id),('state', 'not in', ['done','cancel']),('picking_type_id.code','=','incoming')])
                else:
                    if inter.origin:
                        picking_ids_in = self.env['stock.picking'].search([('origin', '=', inter.origin),('state', 'not in', ['done','cancel']),('picking_type_id.code','=','incoming')])
                if picking_ids_in:
                    reference = picking_ids_in.name
                    for line in inter.move_ids_without_package:
                        move_in = self.env['stock.move'].search([('product_id',"=",line.product_id.id),('reference','=',reference)])
                        if move_in:
                            new_urgent_remain = move_in.urgent_remain
                            if move_in.urgent_remain == move_in.urgent_pick:
                                new_urgent_remain = move_in.urgent_pick - line.quantity_done
                                if new_urgent_remain < 0:
                                    new_urgent_remain = 0
                            else:
                                new_urgent_remain = move_in.urgent_remain - line.quantity_done
                                if new_urgent_remain < 0:
                                    new_urgent_remain = 0
                            new_delivery_done_out = move_in.delivery_done_out + line.quantity_done
                            move_in.update({'delivery_done_out': new_delivery_done_out})
                            move_in.update({'urgent_remain': new_urgent_remain})

    def button_validate(self):
        res = super(Picking, self).button_validate()
        for inter in self:
            if inter.state == "done":
                if inter.picking_type_code == 'incoming' and inter.b_c_urgent_delivery_id:
                    if inter.b_c_urgent_delivery_id and inter.picking_type_id.id == inter.b_c_urgent_delivery_id.from_warehouse.inter_transfer_receive.id:
                        if inter.b_c_urgent_delivery_id.state == 'waiting_delivery':
                            inter.b_c_urgent_delivery_id._update_state()
        return res