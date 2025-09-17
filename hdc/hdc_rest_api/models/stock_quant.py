# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from psycopg2 import Error, OperationalError

from odoo import _, api, fields, models
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

_logger = logging.getLogger(__name__)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    display_name = fields.Char(compute='_compute_display_name', store=True, index=True)

class PickingType(models.Model):
    _inherit = "stock.picking.type"

    is_return = fields.Boolean(string='is return')
    is_requisition = fields.Boolean(string='Is Requisition')

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_return = fields.Boolean(related='picking_type_id.is_return', store=True)

class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_requisition = fields.Boolean(string='Is Requisition')