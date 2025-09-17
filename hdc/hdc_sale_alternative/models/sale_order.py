# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from itertools import groupby
from pytz import timezone, UTC
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang

class SaleOrder(models.Model):
    _inherit = "sale.order"

    # @api.onchange('order_line.product_id')
    def check_low_stock(self):
        self.ensure_one()
        global_discount = self.env['ir.config_parameter'].sudo().get_param('hdc_discount_bernuly.global_discount_default_product_id')
        for order in self:
            for line in order.order_line:
                product = line.product_id
                # เนื่องจากมีเรื่อง globaldiscount มันเลยไปนำมาคิด
                if line.display_type is False :
                    if product.qty_available == 0 and int(product.id) != int(global_discount):
                        return {
                                'name': 'Low Stock',
                                'type': 'ir.actions.act_window',
                                'res_model': 'low.stock.wizard',
                                'view_mode': 'form',
                                'target': 'new',
                                # 'res_id': order.id,
                                'context': {
                                    'default_message_low_stock': f"You Do Not Have Stocks For Product {product.name}",
                                    'default_sale_order_line_id': line.id,
                                },
                            }


    
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_original_id = fields.Many2one(
        'product.product',
        string='Product Original',
    )

    def open_alternative_product_wizard(self):
        alternative_lines = []

        # for replace_product in self.product_id.alternative_ids_m2m:
        #     alternative_lines.append((0, 0, {
        #         'internal_reference': replace_product.default_code,
        #         'bns_code': replace_product.bns_code,
        #         'name': replace_product.name,
        #         'sales_price': replace_product.lst_price,
        #         'on_hand': replace_product.qty_available,
        #         'shipping': replace_product.shipping_qty,
        #         'incoming_qty': replace_product.incoming_qty,
        #     }))

        return {
            'name': 'Alternative Product',
            'type': 'ir.actions.act_window',
            'res_model': 'alternative.product.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_internal_reference': self.product_id.default_code,
                'default_bns_code': self.product_id.bns_code,
                'default_name': self.product_id.name,
                'default_sales_price': self.product_id.lst_price,
                'default_on_hand': self.product_id.qty_available,
                'default_incoming_qty': self.product_id.incoming_qty,
                'default_default_replace_product_ids': self.product_id.alternative_ids_m2m.ids,
                # 'default_alternative_product_ids': alternative_lines,
                'default_sale_order_line_id': self.id,
            },
        } 

    def replace_button(self):
        return True
        
