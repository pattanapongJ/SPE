from odoo import api, models, fields

class BankAccountType(models.Model):
    _inherit = 'res.partner.bank'

    bank_account_type = fields.Char(string='Bank Account Type')
    bank_branch = fields.Char(string='Bank Branch')

