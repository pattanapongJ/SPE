# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare



from werkzeug.urls import url_encode


class Picking(models.Model):
    _inherit = "stock.picking"

    is_urgent = fields.Boolean('Urgent', compute='_compute_is_urgent')
    urgent_delivery_id = fields.Many2one(
        'urgent.delivery', string='Urgent Delivery Transfer',
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help='Batch associated to this transfer', copy=True)

    @api.depends('state')
    def _compute_is_urgent(self):
        for res in self:
            is_urgent = False
            if res.urgent_delivery_id:
                is_urgent = True
    
            res.update({"is_urgent": is_urgent})

    def delivery_out_done_to_in_done(self):
        for inter in self:
            if inter.picking_type_id.code == 'outgoing':
                picking_ids_in = False
                if inter.urgent_delivery_id:
                    picking_ids_in = self.env['stock.picking'].search([('urgent_delivery_id', '=', inter.urgent_delivery_id.id),('state', 'not in', ['done','cancel']),('picking_type_id.code','=','incoming')])
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
                if inter.picking_type_code == 'incoming' and inter.urgent_delivery_id:
                    if inter.urgent_delivery_id and inter.picking_type_id.id == inter.urgent_delivery_id.from_warehouse.inter_transfer_receive.id:
                        pl_list = inter.urgent_delivery_id.picking_list_ids.filtered(lambda l: l.state == "waiting_pick")
                        print('--pl_list--',pl_list)
                        if pl_list:
                            for picking_list in pl_list:
                                print('--for--')
                                picking_list.action_available()
                                picking_list.action_auto_fill()
                                picking_list.action_validate()  # try:  #     picking_list.action_validate()  # except:  #     pass
                        if inter.urgent_delivery_id.state == 'in_progress':
                            inter.urgent_delivery_id._update_state()
        return res

class PickingList(models.Model):
    _inherit = 'picking.lists'

    is_urgent = fields.Boolean('Urgent')
    urgent_delivery_id = fields.Many2one('urgent.delivery', string = 'Urgent Delivery Transfer')

class StockMove(models.Model):
    _inherit = "stock.move"

    qty_remain = fields.Float(string='Store to Stock')