# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    exchange_date_free = fields.Date(string='Free on Board')
    exchange_date = fields.Date(string='Exchange Date')
    rl_count = fields.Integer(string='RL Count', compute='_compute_rl_count')

    def _compute_rl_count(self):
        for move in self:
            rl = self.env['receipt.list']
            for line in move.invoice_line_ids:
                rl |= line.receipt_list_id.receipt_list_id
            move.rl_count = len(rl)

    def open_rl_view(self):
        rl = self.env['receipt.list']
        for line in self.invoice_line_ids:
            rl += line.receipt_list_id.receipt_list_id
        return {
            'name': _('Receipt List'),
            'view_mode': 'tree,form',
            'res_model': 'receipt.list',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', rl.ids)],
        }

class AccountMoveLine(models.Model):
    """ Override AccountInvoice_line to add the link to the purchase order line it is related to"""
    _inherit = 'account.move.line'

    receipt_list_id = fields.Many2one('receipt.list.line', string='Receipt list')
    service_list_id = fields.Many2one('receipt.list.line.service', string='Service List')


class AccountPayment(models.Model):
    _inherit = "account.payment"

    rl_count = fields.Integer(string='RL Count', compute='_compute_rl_count')

    def _compute_rl_count(self):
        for move in self:
            rl = self.env['receipt.list']
            for acc in move.reconciled_bill_ids:
                for line in acc.invoice_line_ids:
                    rl |= line.receipt_list_id.receipt_list_id
            move.rl_count = len(rl)

    def open_rl_view(self):
        rl = self.env['receipt.list']
        for acc in self.reconciled_bill_ids:
            for line in acc.invoice_line_ids:
                rl += line.receipt_list_id.receipt_list_id
        return {
            'name': _('Receipt List'),
            'view_mode': 'tree,form',
            'res_model': 'receipt.list',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', rl.ids)],
        }
