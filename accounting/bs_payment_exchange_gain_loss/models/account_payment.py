# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    partial_payment_gain_loss_entries = fields.One2many(
        string=_('Partial_payment_gain_loss_entries'),
        comodel_name='account.move',
        inverse_name='partial_payment_id',
    )

    partial_gain_loss_entries_count = fields.Integer(string='Partial Gain Loss Count',
                                                     compute='_compute_partial_gain_loss_count')

    @api.depends('partial_payment_gain_loss_entries')
    def _compute_partial_gain_loss_count(self):
        for record in self:
            record.partial_gain_loss_entries_count = len(record.partial_payment_gain_loss_entries)

    def button_open_partial_gain_loss_entries(self):
        self.ensure_one()

        action = {
            'name': _("Partial Exchange Gain Loss Entries"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
        }
        if len(self.partial_payment_gain_loss_entries) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.partial_payment_gain_loss_entries.id,
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', self.partial_payment_gain_loss_entries.ids)],
            })
        return action




class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    
    
    def _create_payments(self):
        return super(AccountPaymentRegister,self.with_context(create_payment_from_wizard=True))._create_payments()