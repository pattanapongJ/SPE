# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, _lt, api, fields, models
from odoo.exceptions import UserError

class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    transit_location = fields.Many2one('stock.location', 'Transit Location', check_company=True)