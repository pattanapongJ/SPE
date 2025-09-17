from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    pdc_receipt_account_id = fields.Many2one('account.account',string='PDC Receipt')
    pdc_payment_account_id = fields.Many2one('account.account',string='PDC Payment')
