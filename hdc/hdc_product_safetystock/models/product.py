from datetime import datetime, timedelta , date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.tools.float_utils import float_round, float_is_zero
import math

class ProductTemplate(models.Model):
    _inherit = "product.template"

    voltage = fields.Char(string='Voltage')

    safe_stock = fields.Float(string='Safe Stock',digits=(16, 2))
    moq_stock = fields.Float(string='MOQ',digits=(16, 2))
    spq_stock = fields.Float(string='SPQ',digits=(16, 2))
