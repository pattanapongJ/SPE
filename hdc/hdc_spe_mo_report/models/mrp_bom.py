# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.tools import float_round
from odoo.exceptions import UserError


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    product_est_qty = fields.Float(string='EST Quantity', default=0.0000,digits=(16,4), required=True)