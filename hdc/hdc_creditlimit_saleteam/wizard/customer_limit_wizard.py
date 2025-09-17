# -*- coding: utf-8 -*-

from odoo import api, fields, models

class customer_limit_wizard(models.TransientModel):
    _inherit = "customer.limit.wizard"
    
    temp_credit_request = fields.Float('Temp Credit Request', compute='_compute_credit_request')
    temp_credit_approved = fields.Float('Temp Credit Approved', compute='_compute_credit_approval')
    credit_limit_show = fields.Float(related='partner_id.credit_limit_show',string="Credit Limit")
    cash_limit_show = fields.Float(related='partner_id.cash_limit_show',string="Cash Limit")
    credit_type = fields.Selection(related='partner_id.credit_type',string="Credit Type")
    credit = fields.Float('Total Credit Receivable (Post Invoice)')
    exceeded_amount = fields.Float('Exceeded Credit Amount')
    exceeded_amount_cash = fields.Float('Exceeded Cash Amount')
    cash = fields.Float('Total Cash Receivable')
    credit_remain = fields.Float(related='partner_id.credit_limit',string="Credit Remain")
    cash_remain = fields.Float(related='partner_id.cash_limit',string="Cash Remain")

    team_id = fields.Many2one('crm.team', string = 'Sales Team')
    credit_limit_show_team = fields.Float(string="Credit Limit")
    credit_team_remain = fields.Float(string="Credit Remain")
    credit_team = fields.Float('Total Credit Receivable (Post Invoice)')
    exceeded_amount_team = fields.Float('Exceeded Credit Amount')

    is_cash = fields.Boolean()
    
    def _compute_credit_request(self):
        for rec in self:
            if self._context.get('order_id'):
                order_id = self.env['sale.order'].browse(self._context.get('order_id'))
            else:
                order_id = self.env['sale.order'].browse(self._context.get('active_id'))
            temp_credit_request = 0
            if order_id:
                credit_request = self.env["temp.credit.request"].search(
                    [("partner_id", "=", order_id.partner_id.id),
                     ("sale_team_id", "=", order_id.team_id.id),
                     ("state", "not in", ("approved", "cancel"))]).mapped("amount_total")
                temp_credit_request = sum(credit_request)
            rec.temp_credit_request = temp_credit_request

    def _compute_credit_approval(self):
        for rec in self:
            if self._context.get('order_id'):
                order_id = self.env['sale.order'].browse(self._context.get('order_id'))
            else:
                order_id = self.env['sale.order'].browse(self._context.get('active_id'))
            temp_credit_approved = 0
            if order_id:
                credit_request = self.env["temp.credit.request"].search(
                    [("partner_id", "=", order_id.partner_id.id),
                     ("sale_team_id", "=", order_id.team_id.id),
                     ("state", "=", "approved")]).mapped("amount_total")
                temp_credit_approved = sum(credit_request)
            rec.temp_credit_approved = temp_credit_approved