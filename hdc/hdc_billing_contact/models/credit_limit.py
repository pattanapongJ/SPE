# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class CreditLimitSalePersonLine(models.Model):
    _inherit = 'credit.limit.sale.person.line'
    _description = "Credit Limit by Sales Person"

    billing_period_id = fields.Many2one(comodel_name='account.billing.period', string="Billing Period")
    payment_period_id = fields.Many2one(comodel_name='account.payment.period', string="Payment Period")
    