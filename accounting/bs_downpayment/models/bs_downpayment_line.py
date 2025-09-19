# -*- coding: utf-8 -*-
import logging

from odoo import models, fields,api
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class BsDownpaymentLine(models.Model):
    _name = 'bs.downpayment.line'
    _description = 'Bs Downpayment Line'
    _check_company_auto = True
    _order = 'payment_date asc'

    downpayment_id = fields.Many2one('bs.downpayment', string='Down Payment', ondelete='cascade')
    payment_date = fields.Date(related='downpayment_id.payment_date')
    move_id = fields.Many2one('account.move',string='Applied Move',copy=False)
    move_line_id = fields.Many2one('account.move.line', string='Applied Move Line', copy=False)
    amount = fields.Float(string='Amount')
    deduct_amount = fields.Float(string='Deduct Amount')
    balance = fields.Float(related='downpayment_id.remaining_balance')
    company_id = fields.Many2one(related='downpayment_id.company_id')


    @api.onchange('deduct_amount')
    def onchange_deduct_amount(self):
        if self.deduct_amount > (self.balance+self.amount):
            raise ValidationError('Deduct Amount should not exceed the Remaining Balance')







