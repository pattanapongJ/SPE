# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    is_taxes_exclude = fields.Boolean(string='Is Taxes Exclude')