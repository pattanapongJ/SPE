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

class WizardRemoveUrgentDelivery(models.TransientModel):
    _name = "wizard.remove.urgent.delivery"
    _description = "Wizard Remove Urgent Delivery Transfer"

    name = fields.Char(string = 'Name', default = "Add Urgent Delivery Transfer")
    urgent_delivery_id = fields.Many2one('urgent.delivery', string = 'Urgent Delivery Transfer')
    picking_id = fields.Many2one('picking.lists', 'Picking List')

    @api.onchange('urgent_delivery_id')
    def _urgent_delivery_id_onchange(self):
        picking_id_domain = [('id','in',self.urgent_delivery_id.picking_list_ids.ids)]
        return {"domain": {"picking_id": picking_id_domain}}
    
    def check_product_id(self,pl_product_list,product_id):
        check_product = False
        for item in pl_product_list:
            if item['product_id'] == product_id.id:
                check_product = True
        return check_product
    
    def check_location_id(self,pl_product_list,product_id,location_id):
        check_location = False
        for item in pl_product_list:
            if item['product_id'] == product_id.id:
                if location_id.id in item['location_id']:
                    check_location = True
        return check_location
    
    def action_remove(self):
        pl_product_list = []
        for pl in self.urgent_delivery_id.picking_list_ids:
            if pl.id != self.picking_id.id:
                for item in pl.list_line_ids:
                    check_product = self.check_product_id(pl_product_list,item.product_id)
                    if check_product:
                        for rec in pl_product_list:
                            if rec['product_id'] == item.product_id.id:
                                rec['location_id'].append(item.location_id.id)
                    else:
                        pl_product_list.append({
                        'product_id': item.product_id.id,
                        'location_id': [item.location_id.id],}
                        )

        self.picking_id.urgent_delivery_id = False

        for item in self.picking_id.list_line_ids:
            product_line = self.urgent_delivery_id.urgent_delivery_line.filtered(
                    lambda a: a.product_id.id == item.product_id.id
                )
            new_urgen_pick_product =  product_line.urgent_pick - item.qty
            product_line.urgent_pick = new_urgen_pick_product
            check_location = self.check_location_id(pl_product_list,item.product_id,item.location_id)
        
            if check_location == False:
                product_line.urgent_location_ids = [(3, item.location_id.id)]
            product_line.picking_list_ids = [(3, self.picking_id.id)]
