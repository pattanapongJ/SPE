# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    barcode_spe_ids = fields.One2many('product.barcode.spe','product_tmpl_id',
        string='Barcode',
        store=True,
    )
    # @api.depends('product_variant_ids')
    # def _compute_barcode_spe_ids(self):
    #     for rec in self:
    #         rec.barcode_spe_ids = self.env['product.barcode.spe'].search([
    #             ('product_tmpl_id', '=', rec.id)
    #         ])

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            # ค้นหาตามฟิลด์พื้นฐานของ product.template และ external_code, barcode_modern_trade จาก product.barcode.spe
            domain = [
                '|', '|', '|', 
                ('name', operator, name),
                ('default_code', operator, name),
                ('barcode', operator, name),
                ('barcode_spe_ids.barcode_modern_trade', operator, name)
            ]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    @api.constrains("default_code")
    def check_duplicate_code(self):
        for obj in self:
            res = self.search([
                ('default_code', '!=', None),
                ('default_code', '=', obj.default_code),
                ('company_id', '=', obj.company_id.id),
            ])
            if len(res) > 1:
                raise UserError(_("Product code / Internal Reference must be unique!"))
                
class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            # ค้นหาตามฟิลด์พื้นฐานของ product.product และ external_code, barcode_modern_trade จาก product.barcode.spe
            domain = [
                '|', '|', '|', '|', 
                ('name', operator, name),
                ('default_code', operator, name),
                ('barcode', operator, name),
                ('product_tmpl_id.barcode_spe_ids.barcode_modern_trade', operator, name)
            ]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

