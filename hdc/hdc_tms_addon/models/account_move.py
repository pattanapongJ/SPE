# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta

class AccountMove(models.Model):
    _inherit = "account.move"

    resend_status = fields.Char("Resend Status")
    remark_billing = fields.Text("Remark Billing Finance ")

    
