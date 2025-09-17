# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class ProductProduct(models.Model):
    _inherit = "product.product"

    # ref_item_number = fields.Char(string='Ref. Item number',index=True)
    # item_eng = fields.Char(string='Item Eng',index=True)
    # online_name = fields.Char(string='Name Online',index=True)
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|','|','|','|','|',('name', operator, name), ('item_eng', operator, name), ('default_code', operator, name),
                      ('barcode', operator, name), ('ref_item_number', operator, name), ('ref_item_fac', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ref_item_number = fields.Char(string='Ref. Item number ax',index=True)
    ref_item_fac = fields.Char(string = 'Ref. Item Fac', index = True)
    item_eng = fields.Char(string='Item Eng',index=True)
    online_name = fields.Char(string='Name Online',index=True)

    box = fields.Integer(string='Box')
    crate = fields.Integer(string='Crate')

    # MASTER CARTON (กล่องนอก)
    master_net_weight = fields.Float(string="Master Net Weight (กก.)")
    master_gross_weight = fields.Float(string="Master Gross Weight (กก.)")
    master_net_weight_uom_id = fields.Many2one('uom.uom', string="master_net_weight_unit")
    master_gross_weight_uom_id = fields.Many2one('uom.uom', string="master_gross_weight_unit")

    # Physical Dimensions
    master_height = fields.Float(string="Master Height (ซม.)")
    master_height_uom_id = fields.Many2one('uom.uom', string="master_height_unit")

    master_width = fields.Float(string="Master Width (กว้าง)")
    master_width_uom_id = fields.Many2one('uom.uom', string="master_width_unit")

    master_length = fields.Float(string="Master Length (ยาว)")
    master_length_uom_id = fields.Many2one('uom.uom', string="master_length_unit")

    master_packing_qty = fields.Float(string="Master Packing QTY")
    master_packing_unit = fields.Many2one('uom.uom', string="master_packing_unit")

    master_packing_qty1 = fields.Char(string="Master Packing QTY 1")

    # INNER CARTON (กล่องใน)
    inner_net_weight = fields.Float(string="Inner Net Weight (กก.)")
    inner_gross_weight = fields.Float(string="Inner Gross Weight (กก.)")
    inner_net_weight_uom_id = fields.Many2one('uom.uom', string="inner_net_weight_unit")
    inner_gross_weight_uom_id = fields.Many2one('uom.uom', string="inner_gross_weight_unit")

    inner_height = fields.Float(string="Inner Height (ซม.)")
    inner_height_uom_id = fields.Many2one('uom.uom', string="inner_height_unit")

    inner_width = fields.Float(string="Inner Width (กว้าง)")
    inner_width_uom_id = fields.Many2one('uom.uom', string="inner_width_unit")

    inner_length = fields.Float(string="Inner Length (ยาว)")
    inner_length_uom_id = fields.Many2one('uom.uom', string="inner_length_unit")

    inner_packing_qty = fields.Float(string="Inner Packing Qty")
    inner_packing_unit = fields.Many2one('uom.uom', string="inner_packing_unit")

    inner_packing_qty1 = fields.Char(string="Inner Packing Qty1")

    # Product + packing size (B-สินค้า + ขนาดบรรจุค้าพร้อมสินค้า)
    b01_weight = fields.Float(string="B01-Weight")
    b01_weight_uom_id = fields.Many2one('uom.uom', string="b01_weight_unit")

    b02_width = fields.Float(string="B02-Width")
    b02_width_uom_id = fields.Many2one('uom.uom', string="b02_width_unit")

    b03_length = fields.Float(string="B03-Length")
    b03_length_uom_id = fields.Many2one('uom.uom', string="b03_length_unit")

    b04_height = fields.Float(string="B04-Height/Depth")
    b04_height_uom_id = fields.Many2one('uom.uom', string="b04_height_unit")

    # C-ขนาดห่อกล่องสินค้าออนไลน์
    online_package_code = fields.Char(string="รหัส")
    online_package_cm = fields.Float(string="ขนาด CM")
    online_package_kg = fields.Float(string="ขนาด KG")
    online_package_weight = fields.Float(string="น้ำหนัก Kg (Online)")

    tags_product_sale_ids = fields.Many2many('crm.tag', string='Tags')
    @api.model
    def default_get(self, fields):
        res = super(ProductTemplate, self).default_get(fields)
        default_tags = self.env['crm.tag'].search([('default_product_tag', '=', True)])
        if default_tags:
            res['tags_product_sale_ids'] = [(6, 0, default_tags.ids)]
        return res


