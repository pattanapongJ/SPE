'''
Created on Nov 16, 2020

@author: Zuhair Hammadi
'''
from odoo import models, fields

class AccountBankStatementGenerate(models.TransientModel):
    _name = "account.bank.statement.generate"
    _description = 'Bank Statement Generate Wizard'
    
    statement_id = fields.Many2one('account.bank.statement')
    journal_id = fields.Many2one(related='statement_id.journal_id')
    payment_ids = fields.Many2many('account.payment')
    invoice_ids = fields.Many2many('account.move')
    
    def process(self):
        for payment in self.payment_ids:
            self.env['account.bank.statement.line'].create({
                'statement_id' : self.statement_id.id,
                'payment_ref' : payment.name,
                'ref' : payment.payment_reference,
                'amount' : payment.payment_type == 'inbound' and payment.amount or -payment.amount,
                'matched_payment_ids' : [(6,0, payment.ids)],
                'date' : payment.date
                })
        
        for invoice in self.invoice_ids:
            amount_residual = invoice.currency_id._convert(invoice.amount_residual, self.statement_id.currency_id, self.statement_id.company_id, self.statement_id.date)
            sign = invoice.is_inbound() and 1 or -1
            self.env['account.bank.statement.line'].create({
                'statement_id' : self.statement_id.id,
                'payment_ref' : invoice.name,
                'ref' : invoice.ref,
                'amount' : self.statement_id.currency_id.round(amount_residual * sign),
                'matched_move_line_ids' : [(6,0, invoice.line_ids.filtered(lambda line : line.account_id.user_type_id.type in ('receivable', 'payable')).ids)],
                'date' : invoice.invoice_date
                })
            