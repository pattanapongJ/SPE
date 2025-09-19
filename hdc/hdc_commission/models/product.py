# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api,fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"
    commission_type_edit = fields.Boolean(string ="Commission Types Edit",compute="_compute_commission_type_edit",)
    commission_type = fields.Many2many('commission.type', string = 'Commission Types',tracking = True,)

    @api.depends("commission_type")
    def _compute_commission_type_edit(self):
        for rec in self:
            commission_type_edit = self.env.user.has_group("hdc_commission.group_commission_manager")
            rec.commission_type_edit = commission_type_edit
