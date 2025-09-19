from odoo import api, fields, models, _
from datetime import datetime

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    receipt_date = fields.Date(string='Receipt Date', default=datetime.today())
    commission_date = fields.Date(string='Commission Date', default=datetime.today())
    internal_note = fields.Text(string="Internal Note")

    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        domain_base = ['|', ('parent_id', '=', False), ('is_company', '=', True)]

        if not self:
            self.partner_id = False
            return

        partner_type = self.partner_type
        domain = domain_base
        if partner_type == 'customer':
            domain += [('customer', '=', True)]
        elif partner_type == 'supplier':
            domain += [('supplier', '=', True)]

        return {'domain': {'partner_id': domain}}



class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        payments = super(AccountPaymentRegister, self)._create_payments()
        for payment in payments:
            payment.receipt_date = default=datetime.today()
            payment.commission_date = default=datetime.today()

        return payments

