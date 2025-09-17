# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    bs_downpayment_id = fields.Many2one('bs.downpayment', string='Down Payment', copy=False, ondelete='restrict')
    bs_downpayment_lines = fields.One2many('bs.downpayment.line', 'move_id', string='Down Payment Line', copy=False,
                                           store=True)


    def button_draft(self):
        res=super(AccountMove,self).button_draft()
        self.bs_onchange_partner_currency()
        return res


    @api.model
    def create(self, values):
        move = super(AccountMove, self).create(values)
        if not move.bs_downpayment_lines:
            move.bs_onchange_partner_currency()
        return move

    def button_cancel(self):
        res = super().button_cancel()
        downpayments = self.mapped('bs_downpayment_id')
        if downpayments:
            downpayments.write({'state': 'confirm'})

        for move in self.filtered(lambda x: x.bs_downpayment_lines):
            move.bs_downpayment_lines.unlink()
        return res

    def _post(self, soft=True):
        res = super()._post(soft=soft)

        self.update_downpayment_value()

        for move in self.filtered(lambda x: x.bs_downpayment_lines):
            ## Recall to make sure when user forget to apply
            move.action_apply_downpayment()
            move.bs_downpayment_lines.filtered(lambda x: x.amount == 0).unlink()

        return res

    def update_downpayment_value(self):
        for move in self.filtered(lambda x: x.bs_downpayment_id):
            val = move._prepare_to_update_downpayment()
            move.bs_downpayment_id.write(val)

    def _prepare_to_update_downpayment(self):
        self.ensure_one()

        return {
            'state': 'post',
            'currency_id':self.currency_id.id,
            'amount':self.amount_total,
            'payment_date':self.invoice_date
        }

    @api.onchange('currency_id', 'partner_id', 'bs_downpayment_id')
    def bs_onchange_partner_currency(self):
        for move in self:
            # move.bs_downpayment_lines =[]
            if move.state != 'draft' or move.bs_downpayment_id or move.move_type not in ['in_invoice', 'out_invoice']:
                continue
            move.bs_downpayment_lines = [(5, 0, 0)]
            _domains = [('partner_id', '=', move.partner_id.id), ('currency_id', '=', move.currency_id.id),
                        ('state', '=', 'post')]
            if move.move_type == 'in_invoice':
                _domains.append(('payment_type', '=', 'outbound'))
            elif move.move_type == 'out_invoice':
                _domains.append(('payment_type', '=', 'inbound'))
            downpayments = self.env['bs.downpayment'].search(_domains)
            to_link_downpayments = downpayments.filtered(lambda x: x.remaining_balance > 0)
            _ids = []
            for dp in to_link_downpayments:
                _ids.append((0, 0, {
                    'downpayment_id': dp.id
                }))

            if _ids:
                move.bs_downpayment_lines = _ids

    def action_apply_downpayment(self):
        self.ensure_one()
        for dp_line in self.bs_downpayment_lines.filtered(lambda x: x.deduct_amount > 0):
            product = dp_line.downpayment_id.product_id
            dp_line.amount = dp_line.deduct_amount
            invoice_line = dp_line.move_line_id
            if dp_line.deduct_amount == invoice_line.price_unit:
                continue

            if not invoice_line:
                new_val = {
                    'product_id': product.id,
                    'quantity': -1,
                    'product_uom_id': product.uom_id.id,
                    'price_unit': dp_line.deduct_amount,
                    'bs_downpayment_line_id': dp_line.id
                }
                self.write({'invoice_line_ids': [(0, 0, new_val)]})
                invoice_line = self.invoice_line_ids.filtered(lambda x: x.bs_downpayment_line_id == dp_line)
            else:
                # invoice_line.with_context(check_move_validity=False,skip_account_move_synchronization=True).write({'price_unit': dp_line.deduct_amount})
                self.write({'invoice_line_ids': [(1, invoice_line.id, {'price_unit': dp_line.deduct_amount})]})


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    bs_downpayment_line_id = fields.Many2one('bs.downpayment.line', string='Down Payment Line',
                                             copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(AccountMoveLine, self).create(vals_list)
        for rec in records:
            if rec.bs_downpayment_line_id:
                rec.bs_downpayment_line_id.write({'move_line_id': rec.id})
        return records
