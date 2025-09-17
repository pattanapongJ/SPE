# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PaymentMultiDeductGroup(models.Model):
    _name = 'payment.multi.deduct.group'
    _description = 'Payment Multi Deduct Group'
    _check_company_auto = True

    name = fields.Char('Payment Multi Deduct Group',copy=True,required=True)
    
    account_lines = fields.One2many(
        string=_('Account Lines'),
        comodel_name='payment.multi.deduct.line',
        inverse_name='group_id',
    )
    user_ids = fields.Many2many('res.users',domain = [('share','=',False)])
    
    company_id = fields.Many2one(
        string=_('Company'),
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company,
        readonly=True
    )

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default.update(
            name=_("%s (copy)") % (self.name or ''))
        return super(PaymentMultiDeductGroup, self).copy(default)

