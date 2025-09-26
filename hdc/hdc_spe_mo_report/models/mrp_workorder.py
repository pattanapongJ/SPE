from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import json

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, format_datetime


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    partner_id = fields.Many2one(related='production_id.partner_id', string="Customer",tracking=True)
    