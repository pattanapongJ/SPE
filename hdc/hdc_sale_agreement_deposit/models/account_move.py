# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, _, api, fields, models

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    sale_agreement_line_id = fields.Many2one('sale.blanket.order.line', 'Sale Agreement Line', ondelete='set null', index=True)
    sale_agreement_id = fields.Many2one('sale.blanket.order', 'Sale Agreement ID', related='sale_agreement_line_id.order_id', readonly=True)
    def unlink(self):
        deposit_line = self.env['sale.blanket.order.line'].search([('id', 'in', self.sale_agreement_line_id.ids)])
        
        for history in deposit_line:
            history.sudo().unlink()
        
        # ลบ record ของ account.move
        return super(AccountMoveLine, self).unlink()
    
class AccountMove(models.Model):
    _inherit = "account.move"

    sale_agreement_id = fields.Many2one(
        comodel_name="sale.blanket.order",
        string="Sale Agreement ID",
        store=True,copy=False,
        ondelete="set null"
    )
    
    def unlink(self):
        deposit_histories = self.env['sale.blanket.deposit.order.history'].search([('deduct_move_id', 'in', self.ids)])

        if deposit_histories:
            deposit_histories.deposit_move_id._compute_deposit_balance()
        
        # ลบ record ของ account.move
        return super(AccountMove, self).unlink()
    
    def action_post(self):
        res = super(AccountMove, self).action_post()
        deposit_histories = self.env['sale.blanket.deposit.order.history'].search([('deduct_move_id', 'in', self.ids)],limit=1)
        history_ids = self.env['sale.order.deposit.history'].search([('deduct_move_id', 'in', self.ids)],limit=1)
        if deposit_histories or history_ids:

            deposit = deposit_histories if deposit_histories else history_ids
            deposit.deposit_move_id._compute_deposit_balance()
        return res

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        deposit_histories = self.env['sale.blanket.deposit.order.history'].search([('deduct_move_id', 'in', self.ids)],limit=1)
        history_ids = self.env['sale.order.deposit.history'].search([('deduct_move_id', 'in', self.ids)],limit=1)
        if deposit_histories or history_ids:

            deposit = deposit_histories if deposit_histories else history_ids
            deposit.deposit_move_id._compute_deposit_balance()
        return res

    @api.depends('state')
    def _compute_deposit_balance(self):
        for move in self:
            domain = [('deduct_move_id', '=', move.id)]
            is_downpayment = False
            if (move.sale_agreement_id and move.sale_agreement_id.line_ids.filtered(lambda l: l.is_deposit)) or move.is_downpayment:
                is_downpayment = True
                domain = [('deposit_move_id', '=', move.id)]
            if is_downpayment:
                history_ids = self.env['sale.order.deposit.history'].search(domain)
                history_blanket_ids = self.env['sale.blanket.deposit.order.history'].search(domain)
                if history_ids or history_blanket_ids:
                    move_deposit_id = history_ids.mapped('deposit_move_id')[0] if history_ids else history_blanket_ids.mapped('deposit_move_id')[0]
                else:
                    move_deposit_id = False
                if history_ids:
                    history_ids = history_ids.filtered(lambda h: h.deduct_move_id.state != 'cancel')
                    deduct_amount = sum(history_ids.mapped('deducted_amount'))
                else:
                    deduct_amount = 0
                if history_blanket_ids:
                    history_blanket_ids = history_blanket_ids.filtered(lambda h: h.deduct_move_id.state != 'cancel')
                    deduct_amount_blanket = sum(history_blanket_ids.mapped('deducted_amount'))
                else:
                    deduct_amount_blanket = 0
                if move_deposit_id:
                    total = sum(move_deposit_id.invoice_line_ids.mapped('price_subtotal'))
                else:
                    if move.sale_agreement_id:
                        total = sum(move.sale_agreement_id.line_ids.filtered(lambda l: l.is_deposit).mapped('price_unit'))
                    else:
                        sale_line_ids = move.invoice_line_ids.filtered(lambda l: l.sale_line_ids[0].is_downpayment and not l.sale_line_ids[0].is_deduct_downpayment if l.sale_line_ids else False).mapped('sale_line_ids')
                        total = sum(sale_line_ids.mapped('price_unit'))

                move.deposit_balance = total - deduct_amount - deduct_amount_blanket
            else:
                move.deposit_balance = 0
                
            