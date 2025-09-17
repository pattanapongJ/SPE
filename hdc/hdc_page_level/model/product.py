# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    page_no = fields.Float(string="Page No.")
    page_number_code = fields.Float(string="Page number code")
    page = fields.Float(string="Page")
    catalog_sel = fields.Char(string="Catalog")
    grouping_sel = fields.Char(string="Grouping Id")

    page_lv1_id = fields.Many2one('product.page.level', string="Page LV 1")
    page_lv1_desc = fields.Char(string="Description", related="page_lv1_id.description", readonly=True)

    page_lv2_id = fields.Many2one('product.page.level', string="Page LV 2")
    page_lv2_desc = fields.Char(string="Description", related="page_lv2_id.description", readonly=True)

    page_lv3_id = fields.Many2one('product.page.level', string="Page LV 3")
    page_lv3_desc = fields.Char(string="Description", related="page_lv3_id.description", readonly=True)

    page_lv4_id = fields.Many2one('product.page.level', string="Page LV 4")
    page_lv4_desc = fields.Char(string="Description", related="page_lv4_id.description", readonly=True)

    status_product = fields.Char(string="สถานะสินค้า")
    expected_date_product = fields.Datetime(string="วันที่ปริมาณการของเข้า")
    page_online = fields.Char(string="Page Online")

