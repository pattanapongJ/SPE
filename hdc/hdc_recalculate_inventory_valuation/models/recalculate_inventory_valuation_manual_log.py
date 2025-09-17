# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
from datetime import datetime
    
class RecalculateInventoryValuationManualLog(models.Model):
    _name = 'recalculate.inventory.valuation.manual.log'
    _description = "Recalculate Inventory Valuation Manual Log"

    recalculate_date = fields.Datetime(string = "Recalculate Date", readonly=True)
    recalculate_by = fields.Many2one('res.users', string = 'Recalculate by', readonly=True)
    total_record = fields.Integer(string="Total Records", help="The number of record to recalculate")
    total_product = fields.Integer(string="Total Products", help="The number of product to recalculate")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self._default_company_id(),index = True,
    )
    start_date = fields.Date(string = 'Start Date', required=True)
    target_type = fields.Selection([
        ('all', 'ALL'),
        ('categ', 'Product Category'),
        ('product', 'Product'),
    ], string="Recalculate Target",default='all')
    categ_id = fields.Many2one("product.category", "Product Category",domain="[('property_cost_method','=','average'),('property_valuation','=','manual_periodic')]")
    product_id = fields.Many2one('product.product', string='Product',domain="[('type', '=', 'product'),('categ_id.property_cost_method','=','average'),('categ_id.property_valuation','=','manual_periodic')]")