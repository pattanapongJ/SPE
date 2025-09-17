from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
import re

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare


class SaleBlanketOrderLine(models.Model):
    _inherit = "sale.blanket.order.line"

    product_ref = fields.Char("Internal Reference", related="product_id.default_code", readonly=True)