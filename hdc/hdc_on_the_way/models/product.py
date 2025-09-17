# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
class ProductTemplate(models.Model):
    _inherit = "product.template"

    shipping_qty = fields.Float(compute='_compute_shipping_qty_template',string='Shipping',digits=(16, 0))
    @api.depends('product_variant_ids.shipping_qty')
    def _compute_shipping_qty_template(self):
        for template in self:
            template.shipping_qty = sum(template.product_variant_ids.mapped('shipping_qty'))
    
class Product(models.Model):
    _inherit = "product.product"

    shipping_qty = fields.Float(compute="_compute_shipping_qty",string='Shipped',digits=(16, 0))
    @api.depends('stock_move_ids', 'stock_move_ids.state')
    def _compute_shipping_qty(self):
        for product in self:
            shipping_qty = sum(
                move.on_the_way for move in product.stock_move_ids if move.state == 'assigned'
            )
            product.shipping_qty = shipping_qty