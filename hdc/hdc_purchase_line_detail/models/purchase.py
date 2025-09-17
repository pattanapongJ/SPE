# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.tools import float_round
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    order_line_detail = fields.One2many('purchase.order.line', 'order_id', string='Order Lines Detail' ,copy=False, auto_join=True)
    
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    categ_id = fields.Many2one('product.category',related='product_id.categ_id', string = 'Product Category')
    hs_code = fields.Char(related='product_id.hs_code', string = 'HS Code')
    item_eng = fields.Char(related='product_id.item_eng', string = 'Eng Name')
    duty_mail = fields.Char(related='user_id.login', string = 'Mail Account')
    product_default_code = fields.Char(related = 'product_id.default_code', store = True)
    tags_product_sale_ids = fields.Many2many(related='product_id.tags_product_sale_ids', string='Tags')
