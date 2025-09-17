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

class WizardAddBoothConsignUrgentDelivery(models.TransientModel):
    _name = "wizard.add.booth.consign.urgent.delivery"
    _description = "Wizard Add Booth Consignment Urgent Delivery Transfer"

    name = fields.Char(string = 'Name', default = "Add Booth Consignment Urgent Delivery Transfer")
    b_c_urgent_delivery_id = fields.Many2one('booth.consign.urgent.delivery', string = 'Booth Consign Urgent Delivery Transfer')
    sale_order_id = fields.Many2one('sale.order', 'Sale Order')

    def action_add(self):
        product_list = []
        
        for product_line in self.b_c_urgent_delivery_id.b_c_urgent_delivery_line:
            product_list.append(product_line.product_id.id)
        
        self.sale_order_id.b_c_urgent_delivery_id = self.b_c_urgent_delivery_id.id
        for item in self.sale_order_id.order_line:
            if item.product_id.id not in product_list and self.b_c_urgent_delivery_id.state == "waiting_delivery":
                raise UserError(
                    _(
                        "Product in SO not in this Booth and Consignment Urgent Delivery"
                    )
                )
            elif item.product_id.id in product_list:
                product_line = self.b_c_urgent_delivery_id.b_c_urgent_delivery_line.filtered(
                    lambda a: a.product_id.id == item.product_id.id
                )
                new_urgen_pick_product =  product_line.urgent_pick + item.product_uom_qty
                if new_urgen_pick_product > product_line.qty and self.b_c_urgent_delivery_id.state == "waiting_delivery":
                    raise UserError(
                    _(
                        "Insufficient quantity in this Urgent Delivery"
                    )
                )
                else:
                    product_line.urgent_pick = new_urgen_pick_product
                    if self.b_c_urgent_delivery_id.state == "in_progress":
                        product_line.qty = product_line.qty + item.product_uom_qty
                    if self.sale_order_id.location_id.id not in product_line.urgent_location_ids.ids:
                        product_line.urgent_location_ids = [(4, self.sale_order_id.location_id.id)]
                    product_line.sale_order_ids = [(4, self.sale_order_id.id)]
            elif item.product_id.id not in product_list:
                product_line = self.env["booth.consign.urgent.delivery.line"]
                product_line.create({
                    "b_c_urgent_delivery_id": self.b_c_urgent_delivery_id.id,
                    "product_id": item.product_id.id,
                    "product_uom": item.product_id.uom_id.id,
                    "qty": item.product_uom_qty,
                    "urgent_pick": item.product_uom_qty,
                    "urgent_location_ids":[self.sale_order_id.location_id.id],
                    "sale_order_ids":[self.sale_order_id.id]
                    })
