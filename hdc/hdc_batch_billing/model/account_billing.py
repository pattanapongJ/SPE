from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo import models, fields, api

class AccountBilling(models.Model):
    _inherit = "account.billing"

    batch_billing_no = fields.Char(string="Batch Biliing No.")
    batch_billing_status = fields.Selection([
        ('wait', 'Waiting Batch'),
        ('done', 'Done')
    ], string='Batch Billing Status', default='wait',tracking=True)