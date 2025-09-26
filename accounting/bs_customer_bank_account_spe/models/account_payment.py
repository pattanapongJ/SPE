# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    customer_bank_id = fields.Many2one('res.partner.bank', string='Customer Bank Account',
                                       compute="_compute_customer_bank_id", store=True, readonly=False)

    @api.depends('partner_id','payment_type','partner_type')
    def _compute_customer_bank_id(self):
        for rec in self:
            if rec.partner_id and rec.payment_type == 'inbound' and rec.partner_type == 'customer':
                bank_ids = rec.partner_id.bank_ids
                if bank_ids:
                    rec.customer_bank_id = bank_ids[0]
                else:
                    rec.customer_bank_id = False
            else:
                rec.customer_bank_id = False


    def action_open_pdc_wizard(self):
        action = super().action_open_pdc_wizard()
        if 'context' in action:
            action['context'].update({'default_customer_bank_id':self.customer_bank_id.id})
        return action




class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    customer_bank_id = fields.Many2one('res.partner.bank', string='Customer Bank Account',
                                       compute="_compute_customer_bank_id", store=True, readonly=False)

    @api.depends('partner_id','payment_type','partner_type')
    def _compute_customer_bank_id(self):
        for rec in self:
            if rec.partner_id and rec.payment_type == 'inbound' and rec.partner_type=='customer':
                bank_ids = rec.partner_id.bank_ids
                if bank_ids:
                    rec.customer_bank_id = bank_ids[0]
                else:
                    rec.customer_bank_id = False
            else:
                rec.customer_bank_id = False

    def _init_payments(self, to_process, edit_mode=False):
        payments = super()._init_payments(to_process, edit_mode)
        payments.write({'customer_bank_id':self.customer_bank_id})
        return payments


    def _prepare_pdc_payment_val(self, payment):
        val = super(AccountPaymentRegister,self)._prepare_pdc_payment_val(payment)
        val['customer_bank_id'] = self.customer_bank_id.id
        return val
