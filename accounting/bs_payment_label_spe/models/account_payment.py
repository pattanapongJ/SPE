from odoo import fields, models

class AccountPaymenMethod(models.Model):
    _inherit = 'account.payment.method'
    
    payment_label = fields.Char(string='Label')