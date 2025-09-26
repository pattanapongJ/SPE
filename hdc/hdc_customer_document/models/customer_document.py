# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ProductHSCode(models.Model):
    _name = "customer.document"
    _description = "Customer Documents"
    _order = "name"

    name = fields.Char(string="แบบที่", required=True)
    note_1 = fields.Text(string="ชุดที่1")
    remark_1 = fields.Text(string="หมายเหตุ1")
    note_2 = fields.Text(string="ชุดที่2")
    remark_2 = fields.Text(string="หมายเหตุ2")
    note_3 = fields.Text(string="ชุดที่3")
    remark_3 = fields.Text(string="หมายเหตุ3")
