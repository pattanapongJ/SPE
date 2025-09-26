# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockLocation(models.Model):
    _inherit = 'stock.location'

    center_return_location = fields.Boolean('Is a Center of Return Location?')
    
    @api.onchange('return_location')
    def _onchange_return_location(self):
        for rec in self:
            if rec.return_location is False:
                rec.center_return_location = False