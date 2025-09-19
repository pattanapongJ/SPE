# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_dewalt = fields.Boolean(string='Is Dewalt')