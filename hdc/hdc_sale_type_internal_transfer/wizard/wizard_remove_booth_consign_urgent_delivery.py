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

class WizardRemoveBoothConsignUrgentDelivery(models.TransientModel):
    _name = "wizard.remove.booth.consign.urgent.delivery"
    _description = "Wizard Remove Booth Consignment Urgent Delivery Transfer"

    name = fields.Char(string = 'Name', default = "Remove Booth Consignment Urgent Delivery Transfer")
    b_c_urgent_delivery_id = fields.Many2one('booth.consign.urgent.delivery', string = 'Booth Consign Urgent Delivery Transfer')
    sale_order_id = fields.Many2one('sale.order', 'Sale Order')

    @api.onchange('b_c_urgent_delivery_id')
    def _b_c_urgent_delivery_id_onchange(self):
        sale_order_id_domain = [('id','in',self.b_c_urgent_delivery_id.sale_order_ids.ids)]
        return {"domain": {"sale_order_id": sale_order_id_domain}}
    
    def check_product_id(self,pl_product_list,product_id):
        check_product = False
        for item in pl_product_list:
            if item['product_id'] == product_id.id:
                check_product = True
        return check_product
    
    def check_location_id(self,product_line,product_id,location_id):
        check_location = False
        for sale_order in product_line.sale_order_ids:
            if sale_order.id != self.sale_order_id:
                if location_id == sale_order.location_id:
                    check_location = True
        return check_location
    
    def action_remove(self):
        pl_product_list = []
        for pl in self.b_c_urgent_delivery_id.sale_order_ids:
            if pl.id != self.sale_order_id.id:
                for item in pl.order_line:
                    check_product = self.check_product_id(pl_product_list,item.product_id)
                    if check_product:
                        for rec in pl_product_list:
                            if rec['product_id'] == item.product_id.id:
                                rec['location_id'].append(self.sale_order_id.location_id.id)
                    else:
                        pl_product_list.append({
                        'product_id': item.product_id.id,
                        'location_id': [self.sale_order_id.location_id.id],}
                        )

        self.sale_order_id.b_c_urgent_delivery_id = False

        for item in self.sale_order_id.order_line:
            product_line = self.b_c_urgent_delivery_id.b_c_urgent_delivery_line.filtered(
                    lambda a: a.product_id.id == item.product_id.id
                )
            new_urgen_pick_product =  product_line.urgent_pick - item.product_uom_qty
            product_line.urgent_pick = new_urgen_pick_product
            if self.b_c_urgent_delivery_id.state == "in_progress":
                product_line.qty = product_line.qty - item.product_uom_qty
            check_location = self.check_location_id(product_line,item.product_id,self.sale_order_id.location_id)
        
            if check_location == False:
                product_line.urgent_location_ids = [(3, self.sale_order_id.location_id.id)]
            product_line.sale_order_ids = [(3, self.sale_order_id.id)]

            if product_line.qty == 0:
                product_line.unlink()
