# -*- coding: utf-8 -*-


import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round
from odoo.tools.float_utils import float_repr
from odoo.tools.misc import format_date
from odoo.exceptions import Warning, ValidationError, UserError, RedirectWarning


class SaleOrder(models.Model):
    _inherit = "sale.order"
    unlock_readonly = fields.Boolean(string="Unlock Readonly", default=False, store=True)

    def action_done(self):
        result = super(SaleOrder, self).action_done()
        for order in self:
            order.unlock_readonly = False
        return result
    
    def action_unlock(self):
        result = super(SaleOrder, self).action_unlock()
        for order in self:
            order.unlock_readonly = True
        return result