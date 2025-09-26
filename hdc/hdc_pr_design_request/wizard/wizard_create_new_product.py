# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models, api
from odoo.osv import expression

class izardPDRNewProductBOM(models.TransientModel):
    _name = 'wizard.pdr.new.product.bom'
    _description = 'Wizard New Product Bom'

    wizard_new_product_id = fields.Many2one(comodel_name="wizard.pdr.new.product",string="SaleEstimateJob",)
    product_id = fields.Many2one("product.product", string="Product" ,domain=[('type', '=', 'product')])
    product_qty = fields.Float(string='Cost', digits='Product Price',required=True,default=1.00)
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure" , required=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.uom_id = self.product_id.uom_id.id

class WizardPDRNewProduct(models.TransientModel):
    _name = 'wizard.pdr.new.product'
    _description = 'Wizard New Product'

    product_name = fields.Char( string='Product Name', required=True)
    categ_id = fields.Many2one('product.category', string='Product Category', required=True)
    default_code = fields.Char( string='Internal Reference')
    design_icon = fields.Char( string='Design Action Icon')
    barcode = fields.Char( string='Barcode')
    sale_cost = fields.Float(string='Cost', digits='Product Price',required=True)
    sale_price = fields.Float(string='Sale Price', digits='Product Price',required=True)
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure" , required=True)
    pdr_id = fields.Many2one('mrp.pdr', string='PDR ID')
    bom_component = fields.One2many(
        comodel_name="wizard.pdr.new.product.bom",
        inverse_name='wizard_new_product_id',
        string="Component",
    )


    def generate_new_product(self):
        bom_line_id = []
        for line in self.bom_component:
            vals = (0, 0,{
                        'product_id':  line.product_id.id,
                        'product_qty': line.product_qty,
                        'uom_id': line.uom_id.id,
                        })
            bom_line_id.append(vals)
        self.env['pdr.product.list.line'].create({
            'product_name': self.product_name,
            'design_icon': self.design_icon,
            'demand_qty': 1.0,
            'uom_id': self.uom_id.id,
            'pdr_id': self.pdr_id.id,
            'categ_id': self.categ_id.id,
            'list_price': self.sale_price,
            'standard_price': self.sale_cost,
            'default_code': self.default_code,
            'barcode': self.barcode,
            'bom_component': bom_line_id,
        })
        
