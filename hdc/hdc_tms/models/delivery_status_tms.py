
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta


class DeliveryStatus(models.Model):
    _name = "delivery.status.tms"

    name = fields.Char('Delivery Status')
    code = fields.Char('Code')