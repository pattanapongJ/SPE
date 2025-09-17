# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class Picking(models.Model):
    _inherit = "stock.picking"

    delivery_list_id = fields.Many2one("distribition.delivery.note", copy=False)