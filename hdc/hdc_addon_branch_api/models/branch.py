# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResBranch(models.Model):
    _inherit = 'res.branch'

    location_id = fields.Many2one('stock.location', 'Source Location',
        domain = "[('usage', 'in', ['internal','production']), ('company_id', 'in', [company_id, False])]",)
    location_dest_id = fields.Many2one('stock.location', 'Destination location',
        domain = "[('usage', 'in', ['internal','production']), ('company_id', 'in', [company_id, False])]",)
    picking_type_id = fields.Many2one(comodel_name="stock.picking.type",string="Requisition Type",)
    picking_type_return_id = fields.Many2one(comodel_name="stock.picking.type",string="Return Type",)
    bank_journal_id = fields.Many2one(comodel_name="account.journal",string="Bank Journal",)
    cash_journal_id = fields.Many2one(comodel_name="account.journal",string="Cash Journal",)


