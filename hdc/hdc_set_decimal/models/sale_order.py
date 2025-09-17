# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from itertools import groupby
from pytz import timezone, UTC
from werkzeug.urls import url_encode
import re
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_uom_qty = fields.Float(string='Quantity', digits='Sale Order', required=True, default=1.0)

    price_unit = fields.Float('Unit Price', required=True, digits='Sale Order', default=0.0)