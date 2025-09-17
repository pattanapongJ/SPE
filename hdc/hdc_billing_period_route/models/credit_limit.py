
from odoo import models, fields

class CreditLimitSaleLine(models.Model):
    _inherit = 'credit.limit.sale.line'

    billing_period_id = fields.Many2one('account.billing.period', string="Billing Period")