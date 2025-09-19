# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class StockProductionLot(models.Model):
    _inherit = "stock.production.lot"

    purchase_claim_line_id = fields.Many2one('purchase.claim.line.ept', string="Purchase Claim line")
