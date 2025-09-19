# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero


class StockLandedCostLine(models.Model):
    _inherit = 'stock.landed.cost.lines'
    _description = 'Stock Landed Cost Line'

    receipt_list_id = fields.Many2one('receipt.list', 'Receipt list', required=False)
    cost_id = fields.Many2one('stock.landed.cost', 'Landed Cost', required=False)
    
class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'
    _description = 'Valuation Adjustment Lines'

    receipt_list_id = fields.Many2one('receipt.list', 'Receipt list', required=False)
    cost_id = fields.Many2one('stock.landed.cost', 'Landed Cost', required=False)