# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    temp_credit_request = fields.Many2one('temp.credit.request', string="Temp Credit Request", compute="compute_temp_credit_request")
    is_cash = fields.Boolean(related='invoice_payment_term_id.is_cash')
    def compute_temp_credit_request(self):
        for rec in self:
            credit_request = self.env['temp.credit.request'].search([('order_no.name', '=', rec.invoice_origin), ('state', '=', "approved")],limit=1)
            if credit_request:
                rec.temp_credit_request = credit_request.id
            else:
                rec.temp_credit_request = False

class AccountPayment(models.Model):
    _inherit = "account.payment"

    is_cheque = fields.Boolean('Is Cheque',related='journal_id.is_cheque')

class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"
    
    is_cash = fields.Boolean('Is Cash',default=False)
    days = fields.Integer('Expiration QT/SA', default=0, help="Number of days before the payment is due.")

class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_cheque = fields.Boolean('Is Cheque',default=False)
