from odoo import fields, models

class AccountPaymenMethod(models.Model):
    _inherit = 'account.move.line'
    
    partner_ref = fields.Char(string='Partner Ref.', store=True)