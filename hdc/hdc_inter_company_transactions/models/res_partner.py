# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, SUPERUSER_ID, _

class Partner(models.Model):
    _inherit = "res.partner"

    inter_company_customer = fields.Boolean(string='Inter Company Transactions Customer')
    inter_company_vendor = fields.Boolean(string='Inter Company Transactions Vendor')