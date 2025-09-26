# Copyright 2020 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models


class AccountWithholdingTax(models.Model):
    _inherit = "account.withholding.tax"
    _check_company_auto = True
    company_id = fields.Many2one('res.company', string='Company', required=True,  default=lambda self: self.env.company)
    