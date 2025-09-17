# -*- coding: utf-8 -*-
from lxml import etree
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

class SettleCommissions(models.Model):
    _name = "settle.commissions"
    _description = "Settle Commissions"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Settle Commissions", default = lambda self: _('New'),tracking = True,)
    team_id = fields.Many2one('crm.team', string = 'Sales Team', tracking = True)
    user_id = fields.Many2one('res.users', string = 'Salesperson', tracking = True, domain="[('id', 'in', member_ids)]")
    sale_spec = fields.Many2one('res.users', string = 'Sale Spec', tracking = True, domain="[('id', 'in', spec_member_ids)]")
    sale_manager_id = fields.Many2one("res.users", string = "Sale Manager", tracking = True, domain="[('id', '=', manager_member_id)]")
    target_type = fields.Selection([
        ('user_id', 'Salesperson'),
        ('sale_spec', 'Sale Spec'),
        ('sale_manager_id', 'Sale Manager or Sales Team'),
    ], string="Commission Target",default='sale_manager_id')

    @api.depends('team_id')
    def _compute_member_ids(self):
        for rec in self:
            rec.member_ids = rec.team_id.member_ids.ids
    member_ids = fields.Many2many('res.users', compute = "_compute_member_ids")

    @api.depends('team_id')
    def _compute_spec_member_ids(self):
        for rec in self:
            rec.spec_member_ids = rec.team_id.sale_spec_member_ids.ids
    spec_member_ids = fields.Many2many('res.users', compute = "_compute_spec_member_ids")

    @api.depends('team_id')
    def _compute_manager_member_ids(self):
        for rec in self:
            rec.manager_member_id = rec.team_id.user_id.id
    manager_member_id = fields.Many2one('res.users', compute = "_compute_manager_member_ids")

    commission_date = fields.Date(string = "Commission Date", tracking = True)
    receipted_date_form = fields.Date(string = "Receipted Date", tracking = True)
    receipted_date_to = fields.Date(string = "Receipted Date To", tracking = True)
    invoice_date_form = fields.Date(string = "Invoice Date", tracking = True)
    invoice_date_to = fields.Date(string = "Invoice Date To", tracking = True)
    period_date = fields.Many2one('sh.account.period', string = 'Period', tracking = True)
    settle_type = fields.Selection([
        ('settle_payment', 'Commission by Payments'),
        ('settle_invoice', 'Commission by Invoices'),
    ], string="Settle Commission Type",default='settle_payment',tracking = True,)

    payment_lines = fields.One2many('settle.commissions.payment.line', 'settle_commissions_id', string = 'Payment Lines')
    invoice_lines = fields.One2many('settle.commissions.invoice.line', 'settle_commissions_id', string = 'Invoice Lines')
    state = fields.Selection(
        [('draft', 'Draft'), ('settled', 'Settled'),('cancel', 'Cancelled'), ], string = 'Status', readonly = True, default = 'draft', tracking = True, )
    
    @api.onchange('team_id')
    def _team_id_onchange(self):
        self.sale_manager_id = self.team_id.user_id.id
        domain_user_id = [('id', 'in', self.team_id.member_ids.ids)]
        domain_sale_manager_id = [('id', '=', self.team_id.user_id.id)]
        domain_sale_spec = [('id', 'in', self.team_id.sale_spec_member_ids.ids)]
        return {'domain': {'user_id': domain_user_id,'sale_manager_id':domain_sale_manager_id,'sale_spec':domain_sale_spec}}
    
    def unlink(self):
        for rec in self:
            if rec.settle_type == "settle_payment":
                for line in rec.payment_lines:
                    if self.target_type == 'user_id':
                        line.payment_id.is_settle_commission_salesperson = False
                    if self.target_type == 'sale_spec':
                        line.payment_id.is_settle_commission_sale_spec = False
                    if self.target_type == 'sale_manager_id':
                        line.payment_id.is_settle_commission_sale_manager = False
            elif rec.settle_type == "settle_invoice":
                for line in rec.invoice_lines:
                    if self.target_type == 'user_id':
                        line.invoice_id.is_settle_commission_salesperson = False
                    if self.target_type == 'sale_spec':
                        line.invoice_id.is_settle_commission_sale_spec = False
                    if self.target_type == 'sale_manager_id':
                        line.invoice_id.is_settle_commission_sale_manager = False
        return super(SettleCommissions, self).unlink()
    
    def confirm_action(self):
        self.write({'state': 'settled'})

    def set_to_draft(self):
        self.write({'state': 'draft'})

    def cancel_action(self):
        if self.settle_type == "settle_payment":
            for line in self.payment_lines:
                if self.target_type == 'user_id':
                    line.payment_id.is_settle_commission_salesperson = False
                if self.target_type == 'sale_spec':
                    line.payment_id.is_settle_commission_sale_spec = False
                if self.target_type == 'sale_manager_id':
                    line.payment_id.is_settle_commission_sale_manager = False
        elif self.settle_type == "settle_invoice":
            for line in self.invoice_lines:
                if self.target_type == 'user_id':
                    line.invoice_id.is_settle_commission_salesperson = False
                if self.target_type == 'sale_spec':
                    line.invoice_id.is_settle_commission_sale_spec = False
                if self.target_type == 'sale_manager_id':
                    line.invoice_id.is_settle_commission_sale_manager = False

        self.write({'state': 'cancel'})

class SettleCommissionsPaymentLine(models.Model):
    _name = "settle.commissions.payment.line"
    _description = "Settle Commissions Payment Line"

    settle_commissions_id = fields.Many2one('settle.commissions', string = 'Settle Commissions')
    selected = fields.Boolean(string="Select")
    payment_id = fields.Many2one('account.payment', string='PDC No.')
    payment_id_create_date = fields.Date(string = "Create PDC")
    payment_id_date = fields.Date(string = "Date Rec.")
    invoice_id = fields.Many2one('account.move', string='Invoice')
    invoice_id_date = fields.Date(string = "INV Date")
    form_no = fields.Char(string="SPE Invoice")
    partner_id = fields.Many2one('res.partner', string = 'ลูกค้า',domain="[('customer', '=', True)]")
    product_id = fields.Many2one('product.product', string='สินค้า')
    total_amount_tax = fields.Float(string = "รับ-รวมภาษี")
    total_amount_untax = fields.Float(string = "รับ-ก่อนภาษี")
    note = fields.Text('หมายเหตุ')

class SettleCommissionsInvoiceLine(models.Model):
    _name = "settle.commissions.invoice.line"
    _description = "Settle Commissions Invoice Line"

    settle_commissions_id = fields.Many2one('settle.commissions', string = 'Settle Commissions')
    selected = fields.Boolean(string="Select")
    invoice_id = fields.Many2one('account.move', string='Invoice')
    invoice_id_date = fields.Date(string = "INV Date")
    form_no = fields.Char(string="SPE Invoice")
    partner_id = fields.Many2one('res.partner', string = 'ลูกค้า')
    product_id = fields.Many2one('product.product', string='สินค้า')
    total_amount_tax = fields.Float(string = "รับ-รวมภาษี")
    total_amount_untax = fields.Float(string = "รับ-ก่อนภาษี")
    note = fields.Text('หมายเหตุ')