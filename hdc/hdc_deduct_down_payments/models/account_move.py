# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.tools import float_is_zero, float_compare

class AccountMove(models.Model):
    _inherit = "account.move"

    deposit_balance = fields.Monetary(string="Deposit Balance", currency_field='currency_id',
                                        compute='_compute_deposit_balance',
                                        help="This field tracks the remaining balance of the deposit.")
    is_downpayment = fields.Boolean(
        string="Is a down payment", help="Down payments are made when creating invoices from a sales order."
        " They are not copied when duplicating a sales order.",copy=False,compute='_compute_is_downpayment')

    def unlink(self):
        res = super(AccountMove, self).unlink()
        deposit_histories = self.env['sale.order.deposit.history'].search([('deduct_move_id', 'in', self.ids)],limit=1)
        if deposit_histories:
            deposit_histories.deposit_move_id._compute_deposit_balance()
        return res
        
    @api.depends('state')
    def _compute_is_downpayment(self):
        for move in self:
            move.is_downpayment = any(move.invoice_line_ids.filtered(lambda l: l.sale_line_ids[0].is_downpayment and not l.sale_line_ids[0].is_deduct_downpayment if l.sale_line_ids else False).mapped('sale_line_ids').mapped('is_downpayment'))
    
    # โดนทับทั้งหมด เพราะมีการหักที่หลายที่
    def _compute_deposit_balance(self):
        for move in self:
            history_ids = self.env['sale.order.deposit.history'].search([('deduct_move_id', '=', move.id)])
            history_ids = history_ids.filtered(lambda h: h.deduct_move_id.state != 'cancel')
            move_deposit_id = history_ids.mapped('deposit_move_id')[0] if history_ids else False
            if move_deposit_id:
                total = sum(move_deposit_id.invoice_line_ids.mapped('price_subtotal'))
            else:
                total = 0
            if history_ids:
                deduct_amount = sum(history_ids.mapped('deducted_amount'))
                move.deposit_balance = total - deduct_amount
            else:
                move.deposit_balance = total

    # def button_cancel(self):
    #     res = super(AccountMove, self).button_cancel()
    #     deposit_histories = self.env['sale.order.deposit.history'].search([('deduct_move_id', 'in', self.ids)],limit=1)
    #     if deposit_histories:
    #         deposit_histories.deposit_move_id._compute_deposit_balance()
    #     return res

    # โดนทับทั้งหมด เพราะมีการหักที่หลายที่
    # def action_post(self):
    #     res = super(AccountMove, self).action_post()
    #     deposit_histories = self.env['sale.order.deposit.history'].search([('deduct_move_id', 'in', self.ids)],limit=1)
    #     if deposit_histories:
    #         deposit_histories.deposit_move_id._compute_deposit_balance()
    #     return res