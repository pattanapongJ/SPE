# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.tools import float_round
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    order_line_detail = fields.One2many('sale.order.line', 'order_id', string='Order Lines Detail' ,copy=False, auto_join=True)
    
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    categ_id = fields.Many2one('product.category',related='product_id.categ_id', string = 'Product Category')
    