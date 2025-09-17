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

class WizardAddUrgentDelivery(models.TransientModel):
    _name = "wizard.add.urgent.delivery"
    _description = "Wizard Add Urgent Delivery Transfer"

    name = fields.Char(string = 'Name', default = "Add Urgent Delivery Transfer")
    urgent_delivery_id = fields.Many2one('urgent.delivery', string = 'Urgent Delivery Transfer')
    picking_id = fields.Many2one('picking.lists', 'Picking List')

    def action_add(self):
        product_list = []
        
        for product_line in self.urgent_delivery_id.urgent_delivery_line:
            product_list.append(product_line.product_id.id)
        
        self.picking_id.urgent_delivery_id = self.urgent_delivery_id.id
        for item in self.picking_id.list_line_ids:
            if item.product_id.id not in product_list:
                raise UserError(
                    _(
                        "Product in PL not in this Urgent Delivery"
                    )
                )
            elif item.product_id.id in product_list:
                product_line = self.urgent_delivery_id.urgent_delivery_line.filtered(
                    lambda a: a.product_id.id == item.product_id.id
                )
                new_urgen_pick_product =  product_line.urgent_pick + item.qty
                if new_urgen_pick_product > product_line.qty:
                    raise UserError(
                    _(
                        "Insufficient quantity in this Urgent Delivery"
                    )
                )
                else:
                    product_line.urgent_pick = new_urgen_pick_product
                    if item.location_id.id not in product_line.urgent_location_ids.ids:
                        product_line.urgent_location_ids = [(4, item.location_id.id)]
                    product_line.picking_list_ids = [(4, self.picking_id.id)]
