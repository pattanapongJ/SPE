# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models
from odoo.tools.float_utils import float_round, float_is_zero
import math
class ProductTemplate(models.Model):
    _inherit = "product.template"

    bill_discount = fields.Boolean('Bill Discount')