from email.policy import default
import json
import time
from ast import literal_eval
from collections import defaultdict
from datetime import date
from itertools import groupby
from operator import attrgetter, itemgetter
from collections import defaultdict
from datetime import datetime

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_datetime
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import format_date


class StockQuantInherit(models.Model):
    _inherit = "stock.quant"

    product_default_code = fields.Char(
        string="Internal Reference",
        related="product_id.default_code",
        store=True,
        readonly=True,
        index=True,
    )

    product_barcode = fields.Char(
        string="Barcode",
        related="product_id.barcode",
        store=True,
        readonly=True,
        index=True,
    )

    product_categ_id = fields.Many2one(
        comodel_name="product.category",
        string="Product Category",
        related="product_id.categ_id",
        store=True,
        readonly=True,
        index=True,
    )