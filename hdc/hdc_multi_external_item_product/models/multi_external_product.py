# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class MultiExternalProduct(models.Model):
    _name = 'multi.external.product'
    _description = "Multi External Item Product"
    
    product_tmpl_id = fields.Many2one('product.template',string='Product Template',required=True)
    name = fields.Char(string='External Item')
    partner_id =  fields.Many2one('res.partner',string='Customer')
    product_description = fields.Text(string='Product Description')
    barcode = fields.Char(string='Barcode')
    qty_package = fields.Integer(string='Unit/Package')
    package = fields.Char(string='Package')
    note = fields.Text(string='Note')
    barcode_modern_trade = fields.Char(string = 'Barcode Modern Trade')
    uom_id = fields.Many2one("uom.uom", string = "Unit of Measure")