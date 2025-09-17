# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ProductHSCode(models.Model):
    _name = "product.hs.code"
    _description = "Product HS Code"
    _order = "name"

    name = fields.Char(string="HS Code", required=True)
    description = fields.Char(string="Description")
    remark = fields.Char(string="Remark")
    duty = fields.Float(string="Duty", default=0, copy=False)
