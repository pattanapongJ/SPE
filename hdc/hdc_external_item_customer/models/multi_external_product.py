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
    partner_id =  fields.Many2one('res.partner',string='Customer',domain=[('customer','=',True)])
    product_description = fields.Text(string='External Descriptions')
    barcode = fields.Char(string='Barcode')
    qty_package = fields.Integer(string='Unit/Package')
    package = fields.Char(string='Package')
    note = fields.Text(string='Note')
    barcode_modern_trade = fields.Char(string = 'Barcode Product')
    uom_id = fields.Many2one("uom.uom", string = "Unit of Measure")

    company_chain_id = fields.Many2one('company.chain', string="Company Chain")

    number_company_chain = fields.Integer(string="Customers", compute="_count_company_chain")

    @api.depends("company_chain_id")
    def _count_company_chain(self):
        for line in self:
            if line.company_chain_id:
                line.number_company_chain = self.env['res.partner'].search_count([('company_chain_id', '=', line.company_chain_id.id)])
            else:
                line.number_company_chain = 0

    def company_chain_customer(self):
        self.ensure_one()
        partners = self.env['res.partner'].search([('company_chain_id', '=', self.company_chain_id.id)]).ids
        return {
            "type": "ir.actions.act_window",
            "name": _("Customers"),
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "target": "current",       
            "domain": [('id', 'in', partners)]     
        }
    
    @api.model
    def create(self, vals):
        res = super(MultiExternalProduct, self).create(vals)     
        if res.name == False:
            res.name = 0
        return res
    
    def write(self, vals):
        if vals.get('name') is False:
            vals['name'] = 0
        res = super(MultiExternalProduct, self).write(vals)
        return res
