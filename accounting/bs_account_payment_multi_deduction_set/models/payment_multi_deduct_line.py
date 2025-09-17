# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PaymentMultiDeductLine(models.Model):
    _name = 'payment.multi.deduct.line'
    _description = 'Payment MultiDeduct Line'
    _check_company_auto = True

    name = fields.Char('Name',required=True)
    account_id = fields.Many2one('account.account',string='Account', required=True)
    group_id = fields.Many2one('payment.multi.deduct.group',string='Group', required=True)
    company_id = fields.Many2one(
        string=_('Company'),
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company,
        readonly=True
    )
    
