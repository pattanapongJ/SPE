# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class ProductPageLevel(models.Model):
    _name = 'product.page.level'

    name = fields.Char(string = 'Name')
    code = fields.Char(string = 'Page LV Code')
    description = fields.Char(string = 'Description')
    note = fields.Text(string = 'Note')
    responsible_id = fields.Many2one("res.users",string = 'Responsible')
    page_lv = fields.Selection(
        selection=[
            ("page1", "Page LV1"),
            ("page2", "Page LV2"),
            ("page3", "Page LV3"),
            ("page4", "Page LV4"),
            ("page5", "Page LV5"),
        ],
        string="Page LV",
    )

    # def name_get(self):
    #     result = []
    #     for record in self:
    #         rec_name = f"Page LV/{record.code}"
    #         result.append((record.id, rec_name))
    #     return result


