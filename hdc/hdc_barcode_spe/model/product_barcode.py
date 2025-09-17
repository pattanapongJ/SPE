# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class ProductBarcodeSPE(models.Model):
    _name = 'product.barcode.spe'
    _description = 'Product Barcode SPE'

    # product_id = fields.Many2one('product.product', string = 'Product')
    product_tmpl_id = fields.Many2one('product.template', string='Product Template',required=True)
    partner_id = fields.Many2one('res.partner', string = 'Customer')
    barcode_modern_trade = fields.Char(string = 'Barcode')
    # external_code = fields.Many2one('multi.external.product',string = 'External')
    ref = fields.Char(string = 'Internal Reference', related='product_tmpl_id.default_code')
    
    external_code = fields.Char(string = 'External')
    external_description = fields.Char(string = 'External Description')
    uom_id = fields.Many2one(
        "uom.uom",
        string="Unit of Measure",
    )
    product_uom_category_id = fields.Many2one(
        'uom.category',
        string="UoM Category",
        related='product_tmpl_id.uom_id.category_id',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        tmpl_id = self._context.get('default_product_tmpl_id')
        if tmpl_id:
            res['product_tmpl_id'] = tmpl_id
        return res
    def name_get(self):
        result = []
        for record in self:
            product_name = record.product_tmpl_id.name if record.product_tmpl_id else ""
            partner_name = record.partner_id.name if record.partner_id else ""
            rec_name = f"[{record.barcode_modern_trade}]({partner_name}) {product_name}"
            result.append((record.id, rec_name))
        return result
    
    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id_set_uom(self):
        if self.product_tmpl_id:
            self.uom_id = self.product_tmpl_id.uom_id