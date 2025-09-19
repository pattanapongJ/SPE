# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class SaleOrderTypology(models.Model):
    _inherit = "sale.order.type"

    modern_trade = fields.Boolean("Modern Trade", default=False)