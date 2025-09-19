from odoo import models, fields, api
from odoo.exceptions import UserError,ValidationError


class GroupPaymentSettle(models.TransientModel):
    _name = 'group.payment.settle'
    _description = 'Group Payment Settle'
    
    payment_register_id = fields.Many2one('account.payment.register', string='Payment Register')
    move_id = fields.Many2one('account.move', string='Number',readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency',related='payment_register_id.currency_id')
    settle_amount = fields.Monetary(string='Settle Amount',required=True)
    due_amount = fields.Monetary(string='Amount Due',compute='_compute_due_amount')
    balance = fields.Monetary(string='Balance',compute='_compute_balance')
    
    
    
    @api.depends('due_amount','settle_amount')
    def _compute_balance(self):
        for rec in self:
            rec.balance = rec.due_amount - rec.settle_amount
    
    
    
    @api.depends('move_id','currency_id','payment_register_id.payment_date')
    def _compute_due_amount(self):
        for record in self:
            source_currency_id = record.move_id.currency_id
            if source_currency_id == record.currency_id:
                record.due_amount = record.move_id.amount_residual
            else:
                record.due_amount = source_currency_id._convert(record.move_id.amount_residual, record.currency_id, record.move_id.company_id, record.payment_register_id.payment_date or fields.Date.today())
                record.settle_amount = source_currency_id._convert(record.settle_amount, record.currency_id, record.move_id.company_id, record.payment_register_id.payment_date or fields.Date.today())
    

    @api.constrains('settle_amount','due_amount')
    def _check_settle_amount(self):
        for record in self:
            if record.settle_amount <= 0:
                raise ValidationError(f'Settle amount of {record.move_id.name} must be greater than zero')
            if record.settle_amount > record.due_amount:
                raise ValidationError(f'Settle amount of {record.move_id.name} must be less than or equal to due amount')