# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.onchange('partner_type')
    def onchange_partner_type(self):
        _domain = []
        if self.partner_type in ['customer']:
            _domain = [('show_in_sale', '=', True)]
        elif self.partner_type in ['supplier']:
            _domain = [('show_in_purchase', '=', True)]
        return {'domain': {'currency_id': _domain}}


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    @api.onchange('partner_type')
    def onchange_partner_type(self):
        _domain = []
        if self.partner_type in ['customer']:
            _domain = [('show_in_sale', '=', True)]
        elif self.partner_type in ['supplier']:
            _domain = [('show_in_purchase', '=', True)]
        return {'domain': {'currency_id': _domain}}



