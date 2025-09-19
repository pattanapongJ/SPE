# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountIncoterms(models.Model):
    _inherit = 'account.incoterms'

    description = fields.Char(string="Description")