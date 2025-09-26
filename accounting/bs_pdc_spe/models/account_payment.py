# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    due_date = fields.Date(string='Due Date',default=fields.Date.context_today)
    bank_id = fields.Many2one('res.bank', string='Bank',store=True,readonly=False,compute='_compute_default_bank_info')
    bank_branch = fields.Char('Bank Branch',store=True,readonly=False,compute='_compute_default_bank_info')


    @api.depends('partner_id')
    def _compute_default_bank_info(self):
        for rec in self:
            bank, bank_branch = rec._get_default_bank_info_for_pdc()
            rec.bank_id = bank
            rec.bank_branch = bank_branch


    def _get_default_bank_info_for_pdc(self):
        partner_banks = self.partner_id.bank_ids
        for p_bank in partner_banks:
            return p_bank.bank_id,p_bank.bank_branch
        return None,None


    def _prepare_pdc_payment_val(self, payment):
        val = super(AccountPaymentRegister, self)._prepare_pdc_payment_val(payment)

        default_bank,default_bank_branch =self._get_default_bank_info_for_pdc()
        bank = self.bank_id or default_bank
        bank_branch = self.bank_branch or default_bank_branch
        val['due_date'] = self.due_date
        val['bank_id'] = bank.id
        val['bank_branch'] = bank_branch
        return val
