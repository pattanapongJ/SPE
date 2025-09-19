from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = "account.move"

    batch_billing_id = fields.Many2one('batch.billing', string='Batch Billing ID')