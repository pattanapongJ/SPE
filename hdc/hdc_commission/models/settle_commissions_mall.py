# -*- coding: utf-8 -*-
from lxml import etree
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

class SettleCommissionsMall(models.Model):
    _name = "settle.commissions.mall"
    _description = "Settle Commissions Mall"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Settle Commissions Mall", default = lambda self: _('New'),tracking = True,)
    team_id = fields.Many2one('crm.team', string = 'Sales Team', tracking = True)
    user_id = fields.Many2one('res.users', string = 'Salesperson', tracking = True, domain="[('id', 'in', member_ids)]")
    sale_spec = fields.Many2one('res.users', string = 'Sale Spec', tracking = True, domain="[('id', 'in', spec_member_ids)]")
    sale_manager_id = fields.Many2one("res.users", string = "Sale Manager", tracking = True, domain="[('id', '=', manager_member_id)]")
    target_type_commission = fields.Selection([
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
    
    target_type = fields.Selection([
        ('normal', 'Normal'),
        ('sold_out', 'Sold Out'),
    ], string="Commission Type",default='normal')

    commission_date = fields.Date(string = "Commission Date", tracking = True)
    receipted_date_form = fields.Date(string = "Receipted Date", tracking = True)
    receipted_date_to = fields.Date(string = "Receipted Date To", tracking = True)
    invoice_date_form = fields.Date(string = "Invoice Date", tracking = True)
    invoice_date_to = fields.Date(string = "Invoice Date To", tracking = True)
    period_date = fields.Many2one('sh.account.period', string = 'Period', tracking = True)

    commission_lines = fields.One2many('settle.commissions.mall.line', 'settle_commissions_mall_id', string = 'Commission Lines')
    payment_lines = fields.One2many('settle.commissions.mall.payment.line', 'settle_commissions_mall_id', string = 'Payment Lines')

    commission_sold_out_lines = fields.One2many('settle.commissions.mall.sold.out.line', 'settle_commissions_mall_id', string = 'Commission Sold Out Lines')
    invoice_lines = fields.One2many('settle.commissions.mall.invoice.line', 'settle_commissions_mall_id', string = 'Invoice Lines')
    
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
            if rec.target_type == "normal":
                for line in rec.payment_lines:
                    line.payment_id.is_settle_commission_mall = False
            elif rec.target_type == "sold_out":
                for line in rec.invoice_lines:
                    line.invoice_id.is_settle_commission_mall = False
        return super(SettleCommissionsMall, self).unlink()
    
    def confirm_action(self):
        self.write({'state': 'settled'})

    def set_to_draft(self):
        self.write({'state': 'draft'})

    def cancel_action(self):
        if self.target_type == "normal":
            for line in self.payment_lines:
                line.payment_id.is_settle_commission_mall = False
        elif self.target_type == "sold_out":
           for line in self.invoice_lines:
                    line.invoice_id.is_settle_commission_mall = False

        self.write({'state': 'cancel'})

class SettleCommissionsMallPaymentLine(models.Model):
    _name = "settle.commissions.mall.payment.line"
    _description = "Settle Commissions Mall Payment Line"

    settle_commissions_mall_id = fields.Many2one('settle.commissions.mall', string = 'Settle Commissions Mall')
    selected = fields.Boolean(string="Select")
    payment_id = fields.Many2one('account.payment', string='PDC No.')
    payment_id_create_date = fields.Date(string = "Create PDC")
    payment_id_date = fields.Date(string = "Date Rec.")
    invoice_id = fields.Many2one('account.move', string='Invoice')
    invoice_id_date = fields.Date(string = "INV Date")
    form_no = fields.Char(string="SPE Invoice")
    partner_id = fields.Many2one('res.partner', string = 'ลูกค้า',domain="[('customer', '=', True)]")
    company_id = fields.Many2one('res.company', string='Company')
    product_id = fields.Many2one('product.product', string='สินค้า')
    total_amount_tax = fields.Float(string = "รับ-รวมภาษี")
    total_amount_untax = fields.Float(string = "รับ-ก่อนภาษี")
    note = fields.Text('หมายเหตุ')

class SettleCommissionsMallInvoiceLine(models.Model):
    _name = "settle.commissions.mall.invoice.line"
    _description = "Settle Commissions Mall Invoice Line"

    settle_commissions_mall_id = fields.Many2one('settle.commissions.mall', string = 'Settle Commissions Mall')
    selected = fields.Boolean(string="Select")
    invoice_id = fields.Many2one('account.move', string='Invoice')
    invoice_id_date = fields.Date(string = "INV Date")
    form_no = fields.Char(string="SPE Invoice")
    partner_id = fields.Many2one('res.partner', string = 'ลูกค้า')
    company_id = fields.Many2one('res.company', string='Company')
    product_id = fields.Many2one('product.product', string='สินค้า')
    total_amount_tax = fields.Float(string = "รับ-รวมภาษี")
    total_amount_untax = fields.Float(string = "รับ-ก่อนภาษี")
    note = fields.Text('หมายเหตุ')

class SettleCommissionsMallLine(models.Model):
    _name = "settle.commissions.mall.line"
    _description = "Settle Commissions Mall Line"

    settle_commissions_mall_id = fields.Many2one('settle.commissions.mall', string = 'Settle Commissions Mall')
    payment_id = fields.Many2one('account.payment', string='เลขที่เอกสาร (รับชำระ) ')
    payment_id_date = fields.Date(string = "Date รับชำระ")
    company_id = fields.Many2one('res.company', string='นิติ')
    partner_id = fields.Many2one('res.partner', string = 'รายชื่อลูกค้า',domain="[('customer', '=', True)]")
    total_amount_tax = fields.Float(string = "รับชำระ (รวมภาษี)")
    total_amount_untax = fields.Float(string = "รับชำระ (ก่อนภาษี)")
    note = fields.Text('หมายเหตุ')

class SettleCommissionsMallSoldOutLine(models.Model):
    _name = "settle.commissions.mall.sold.out.line"
    _description = "Settle Commissions Mall Sold Out Line"

    settle_commissions_mall_id = fields.Many2one('settle.commissions.mall', string = 'Settle Commissions Mall')
    partner_id = fields.Many2one('res.partner', string = 'รายชื่อลูกค้า')
    company_id = fields.Many2one('res.company', string='นิติ')
    
    sold_out_amount_tax = fields.Float(string = "Sold Out มูลค่า(รวมภาษี)")
    sold_out_amount_untax = fields.Float(string = "Sold Out มูลค่า(ก่อนภาษี)")
    expenses_rate = fields.Text('Expenses Rate')
    expenses_value = fields.Float(string = "Expenses Value")
    total_amount_untax_cn = fields.Float(string = "CN/ก่อนภาษี")
    cal_com_value = fields.Float(string = "Cal.COM Value")
    commission_rate = fields.Text('Commission Rate')
    commission_value = fields.Float(string = "Commission Value")
    deduct_commission = fields.Float(string = "หัก Commission")