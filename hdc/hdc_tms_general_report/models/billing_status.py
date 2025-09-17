
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta


class BillingStatus(models.Model):
    _name = "billing.status"

    name = fields.Char('Billing Status')