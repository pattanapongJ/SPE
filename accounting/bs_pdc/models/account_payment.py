# -*- coding: utf-8 -*
from odoo import models, fields


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    cheque_ref = fields.Char('Cheque Reference')
    is_pdc_journal = fields.Boolean(related='journal_id.pdc_journal_checkbox')

    def _create_payments(self):
        payments = super()._create_payments()
        icpSudo = self.env['ir.config_parameter'].sudo()
        allow_automatic_pdc_creation = icpSudo.get_param('bs_pdc.allow_automatic_pdc_creation')
        if not allow_automatic_pdc_creation:
            return payments
        for payment in payments.filtered(lambda x: x.journal_id.pdc_journal_checkbox):
            _val = self._prepare_pdc_payment_val(payment)
            pdc_id = self.env['pdc.wizard'].create(_val)
            payment.write({'pdc_id': pdc_id.id})
        return payments

    def _prepare_pdc_payment_val(self, payment):
        return {
            'payment_amount': payment.amount,
            'payment_type': 'send_money' if payment.payment_type == 'outbound' else 'receive_money',
            'partner_id': payment.partner_id.id,
            'due_date': payment.date,
            'pdc_effective_date': False,
            'payment_date': payment.date,
            'reference': self.cheque_ref
        }
