# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

class MultiExternalProduct(models.Model):
    _inherit = 'multi.external.product'

    barcode_spe_ids = fields.One2many(related="product_tmpl_id.barcode_spe_ids", string="Barcode Product")
    barcode_modern_trade = fields.Char(string = 'Barcode Customer')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    external_product_ids = fields.One2many('multi.external.product', 'product_tmpl_id', string='External Products')