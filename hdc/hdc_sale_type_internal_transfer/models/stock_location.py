# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_retail = fields.Boolean(string='Is Retail')
    is_booth = fields.Boolean(string='Is Booth & Consignment')