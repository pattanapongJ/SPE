# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    
    multi_deduct_group_id = fields.Many2one('payment.multi.deduct.group',string='Multi Deduct Group', domain=lambda self: self._get_multi_deduct_group_domain())

    @api.model
    def _get_multi_deduct_group_domain(self):
        allowed_groups = self.env['payment.multi.deduct.group'].search([('user_ids','in',self.env.user.ids)])
        return [('id', 'in', allowed_groups.ids)]

    @api.onchange('multi_deduct_group_id')
    def onchange_multi_deduct_group_id(self):
        self.deduction_ids.update({'multi_deduct_group_line_id':None,'account_id':None})


