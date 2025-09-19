# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, OrderedSet

import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    new_date_cost = fields.Datetime(string="Add Date Cost",copy=False)

    @api.onchange('new_date_cost')
    def _onchange_new_date_cost(self):
        for rec in self:
            if rec.new_date_cost:
                for line in rec.move_lines:
                    line.new_date_cost = rec.new_date_cost
