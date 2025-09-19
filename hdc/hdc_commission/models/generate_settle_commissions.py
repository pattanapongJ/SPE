# -*- coding: utf-8 -*-
from lxml import etree
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

class GenerateSettleCommissions(models.Model):
    _name = "generate.settle.commissions"
    _description = "Generate Settle Commissions"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Generate Settle Commissions", readonly=True, default='Generate Settle Commissions')
    team_id = fields.Many2one('crm.team', string = 'Sales Team')
    user_id = fields.Many2one('res.users', string = 'Salesperson', domain="[('id', 'in', member_ids)]")
    sale_spec = fields.Many2one('res.users', string = 'Sale Spec', domain="[('id', 'in', spec_member_ids)]")
    sale_manager_id = fields.Many2one("res.users", string = "Sale Manager", domain="[('id', '=', manager_member_id)]")
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

    receipted_date_form = fields.Date(string = "Receipted Date")
    receipted_date_to = fields.Date(string = "Receipted Date To")
    invoice_date_form = fields.Date(string = "Invoice Date")
    invoice_date_to = fields.Date(string = "Invoice Date To")
    settle_type = fields.Selection([
        ('settle_payment', 'Commission by Payments'),
        ('settle_invoice', 'Commission by Invoices'),
    ], string="Settle Commission Type",default='settle_payment')

    selected = fields.Boolean(string = "Select All")
    payment_lines = fields.One2many('generate.settle.commissions.payment.line', 'generate_settle_commissions_id', string = 'Payment Lines')
    invoice_lines = fields.One2many('generate.settle.commissions.invoice.line', 'generate_settle_commissions_id', string = 'Invoice Lines')

    @api.onchange('team_id')
    def _team_id_onchange(self):
        self.sale_manager_id = self.team_id.user_id.id
        domain_user_id = [('id', 'in', self.team_id.member_ids.ids)]
        domain_sale_manager_id = [('id', '=', self.team_id.user_id.id)]
        domain_sale_spec = [('id', 'in', self.team_id.sale_spec_member_ids.ids)]
        return {'domain': {'user_id': domain_user_id,'sale_manager_id':domain_sale_manager_id,'sale_spec':domain_sale_spec}}
    
    @api.onchange('selected')
    def _selected_onchange(self):
        if self.selected:
            if self.settle_type == "settle_payment":
                for line in self.payment_lines:
                    line.selected = True
            elif self.settle_type == "settle_invoice":
                for line in self.invoice_lines:
                    line.selected = True
        else:
            if self.settle_type == "settle_payment":
                for line in self.payment_lines:
                    line.selected = False
            elif self.settle_type == "settle_invoice":
                for line in self.invoice_lines:
                    line.selected = False

    def search_action(self):
        user_company = self.env.context['allowed_company_ids']
        all_company = self.env['res.company'].search([])

        if len(user_company) < len(all_company):
            raise UserError('Not Allow Please Change to Multi Companies')
        
        self.payment_lines = False
        self.invoice_lines = False
        self.selected = False
        domain_search = [('state', '=', 'posted')]

        if self.target_type == 'user_id':
            domain_search += [('is_settle_commission_salesperson', '=',False)]
        if self.target_type == 'sale_spec':
            domain_search += [('is_settle_commission_sale_spec', '=',False)]
        if self.target_type == 'sale_manager_id':
            domain_search += [('is_settle_commission_sale_manager', '=',False)]

        if self.settle_type == "settle_payment":
            if self.receipted_date_form:
                if self.receipted_date_to and self.receipted_date_to < self.receipted_date_form:
                    raise UserError(_("The end date cannot be less than the start date."))
                domain_search += [('date', '>=', self.receipted_date_form)]
        
            if self.receipted_date_to:
                domain_search += [('date', '<=', self.receipted_date_to)]
            payment_ids = self.env['account.payment'].search(domain_search + [],order="date asc")
            order_line = []
            
            for payment in payment_ids:
                if payment.reconciled_invoice_ids:
                    
                    for invoice in payment.reconciled_invoice_ids:
                        check_invoice_date = True
                        check_team_id = True
                        check_user_id = True
                        check_sale_spec = True
                        check_sale_manager_id = True
                        if self.invoice_date_form:
                            if self.invoice_date_to and self.invoice_date_to < self.invoice_date_form:
                                raise UserError(_("The end date cannot be less than the start date."))
                            if invoice.invoice_date < self.invoice_date_form:
                                check_invoice_date = False
                        
                        if self.invoice_date_to:
                            if invoice.invoice_date > self.invoice_date_to:
                                check_invoice_date = False

                        if self.team_id:
                            if invoice.team_id != self.team_id:
                                check_team_id = False

                        if self.user_id and self.target_type == 'user_id':
                            if invoice.invoice_user_id != self.user_id:
                                check_user_id = False

                        if self.sale_spec and self.target_type == 'sale_spec':
                            if invoice.sale_spec != self.sale_spec:
                                check_sale_spec = False
                        
                        if self.sale_manager_id and self.target_type == 'sale_manager_id':
                            if invoice.team_id.user_id != self.sale_manager_id:
                                check_sale_manager_id = False

                        if check_invoice_date and check_team_id and check_user_id and check_sale_spec and check_sale_manager_id:
                            for invoice_line in invoice.invoice_line_ids:
                                if invoice_line.product_id.type != 'service':
                                    total_amount_tax = invoice_line.price_total
                                    total_amount_untax = invoice_line.price_subtotal
                                            
                                    line = (0, 0, {
                                        'generate_settle_commissions_id': self.id,
                                        'payment_id': payment.id,
                                        'payment_id_create_date': payment.create_date.date(),
                                        'payment_id_date': payment.date,
                                        'invoice_id': invoice.id,
                                        'invoice_id_date': invoice.invoice_date,
                                        'form_no': invoice.form_no,
                                        'partner_id': invoice.partner_id.id,
                                        'product_id': invoice_line.product_id.id,
                                        'total_amount_tax': total_amount_tax,
                                        'total_amount_untax': total_amount_untax,
                                    })
                                    order_line.append(line)

            self.write({
                'payment_lines': order_line
            })
        elif self.settle_type == "settle_invoice":
            domain_search += [('move_type', '=', 'out_invoice')]
            invoice_ids = self.env['account.move'].search(domain_search + [],order="invoice_date asc")
            order_line = []
            
            for invoice in invoice_ids:                   
                check_invoice_date = True
                check_team_id = True
                check_user_id = True
                check_sale_spec = True
                check_sale_manager_id = True
                if self.invoice_date_form:
                    if self.invoice_date_to and self.invoice_date_to < self.invoice_date_form:
                        raise UserError(_("The end date cannot be less than the start date."))
                    if invoice.invoice_date < self.invoice_date_form:
                        check_invoice_date = False
                
                if self.invoice_date_to:
                    if invoice.invoice_date > self.invoice_date_to:
                        check_invoice_date = False

                if self.team_id:
                    if invoice.team_id != self.team_id:
                        check_team_id = False

                if self.user_id and self.target_type == 'user_id':
                    if invoice.invoice_user_id != self.user_id:
                        check_user_id = False

                if self.sale_spec and self.target_type == 'sale_spec':
                    if invoice.sale_spec != self.sale_spec:
                        check_sale_spec = False
                
                if self.sale_manager_id and self.target_type == 'sale_manager_id':
                    if invoice.team_id.user_id != self.sale_manager_id:
                        check_sale_manager_id = False

                if check_invoice_date and check_team_id and check_user_id and check_sale_spec and check_sale_manager_id:
                    for invoice_line in invoice.invoice_line_ids:
                        if invoice_line.product_id.type != 'service':
                            total_amount_tax = invoice_line.price_total
                            total_amount_untax = invoice_line.price_subtotal
                                    
                            line = (0, 0, {
                                'generate_settle_commissions_id': self.id,
                                'invoice_id': invoice.id,
                                'invoice_id_date': invoice.invoice_date,
                                'form_no': invoice.form_no,
                                'partner_id': invoice.partner_id.id,
                                'product_id': invoice_line.product_id.id,
                                'total_amount_tax': total_amount_tax,
                                'total_amount_untax': total_amount_untax,
                            })
                            order_line.append(line)

            self.write({
                'invoice_lines': order_line
            })

    def clear_all_action(self):
        self.team_id = False
        self.user_id = False
        self.sale_spec = False
        self.sale_manager_id = False

        self.receipted_date_form = False
        self.receipted_date_to = False
        self.invoice_date_form = False
        self.invoice_date_to = False
        self.payment_lines = False
        self.invoice_lines = False
        self.selected = False

    def create_settlements(self):
        user_company = self.env.context['allowed_company_ids']
        all_company = self.env['res.company'].search([])

        if len(user_company) < len(all_company):
            raise UserError('Not Allow Please Change to Multi Companies')
        
        return {
                'name': _('Make Settlements?'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'wizard.create.settlements',
                'view_mode': 'form',
                'target': 'new',
                'context': {"default_generate_settle_commissions_id": self.id,
                            "default_team_id": self.team_id.id,
                            "default_user_id": self.user_id.id,
                            "default_sale_spec": self.sale_spec.id,
                            "default_sale_manager_id": self.sale_manager_id.id,
                            "default_target_type": self.target_type,
                            "default_settle_type": self.settle_type,},
            }
    
    def create_new_settlements(self):
        payment_lines = []
        invoice_lines = []
        if self.settle_type == "settle_payment":
            select_payment_lines = self.payment_lines.filtered(lambda l: l.selected)
            for line in select_payment_lines:
                if self.target_type == 'user_id':
                    line.payment_id.is_settle_commission_salesperson = True
                if self.target_type == 'sale_spec':
                    line.payment_id.is_settle_commission_sale_spec = True
                if self.target_type == 'sale_manager_id':
                    line.payment_id.is_settle_commission_sale_manager = True

                payment_lines.append((0, 0, {
                    'payment_id': line.payment_id.id,
                    'payment_id_create_date': line.payment_id_create_date,
                    'payment_id_date': line.payment_id_date,
                    'invoice_id': line.invoice_id.id,
                    'invoice_id_date': line.invoice_id_date,
                    'form_no': line.form_no,
                    'partner_id': line.partner_id.id,
                    'product_id': line.product_id.id,
                    'total_amount_tax': line.total_amount_tax,
                    'total_amount_untax': line.total_amount_untax,
                    'note': line.note,
                    }))
        elif self.settle_type == "settle_invoice":
            select_invoice_lines = self.invoice_lines.filtered(lambda l: l.selected)
            for line in select_invoice_lines:
                if self.target_type == 'user_id':
                    line.invoice_id.is_settle_commission_salesperson = True
                if self.target_type == 'sale_spec':
                    line.invoice_id.is_settle_commission_sale_spec = True
                if self.target_type == 'sale_manager_id':
                    line.invoice_id.is_settle_commission_sale_manager = True
                    
                invoice_lines.append((0, 0, {
                    'invoice_id': line.invoice_id.id,
                    'invoice_id_date': line.invoice_id_date,
                    'form_no': line.form_no,
                    'partner_id': line.partner_id.id,
                    'product_id': line.product_id.id,
                    'total_amount_tax': line.total_amount_tax,
                    'total_amount_untax': line.total_amount_untax,
                    'note': line.note,
                    }))
        commission_date = datetime.now()
        
        user_id = False
        sale_spec = False
        sale_manager_id = False

        if self.target_type == 'user_id':
            user_id = self.user_id.id
        if self.target_type == 'sale_spec':
            sale_spec = self.sale_spec.id
        if self.target_type == 'sale_manager_id':
            sale_manager_id = self.sale_manager_id.id
        
        settle_commission = {
            'team_id': self.team_id.id, 
            'target_type':self.target_type,
            'user_id': user_id,
            'sale_spec': sale_spec, 
            'sale_manager_id': sale_manager_id,
            'commission_date':commission_date,
            'receipted_date_form': self.receipted_date_form, 
            'receipted_date_to': self.receipted_date_to,
            'invoice_date_form': self.invoice_date_form, 
            'invoice_date_to': self.invoice_date_to,
            'settle_type': self.settle_type,
            'payment_lines': payment_lines,
            'invoice_lines': invoice_lines,
            }

        settle_commission_id = self.env['settle.commissions'].create(settle_commission)
        action = {
            'name': 'Settle Commissions',
            'type': 'ir.actions.act_window',
            'res_model': 'settle.commissions',
            'res_id': settle_commission_id.id, 'view_mode': 'form',
            }
        return action
    
    def add_to_settlements(self,settle_commissions_id=None):
        if self.settle_type == "settle_payment":
            settle_commissions_payment_line = self.env["settle.commissions.payment.line"]
            select_payment_lines = self.payment_lines.filtered(lambda l: l.selected)
            
            for line in select_payment_lines:
                if self.target_type == 'user_id':
                    line.payment_id.is_settle_commission_salesperson = True
                if self.target_type == 'sale_spec':
                    line.payment_id.is_settle_commission_sale_spec = True
                if self.target_type == 'sale_manager_id':
                    line.payment_id.is_settle_commission_sale_manager = True

                settle_commissions_payment_line.create({
                    'settle_commissions_id':settle_commissions_id,
                    'payment_id': line.payment_id.id,
                    'payment_id_create_date': line.payment_id_create_date,
                    'payment_id_date': line.payment_id_date,
                    'invoice_id': line.invoice_id.id,
                    'invoice_id_date': line.invoice_id_date,
                    'form_no': line.form_no,
                    'partner_id': line.partner_id.id,
                    'product_id': line.product_id.id,
                    'total_amount_tax': line.total_amount_tax,
                    'total_amount_untax': line.total_amount_untax,
                    'note': line.note,
                    })
        elif self.settle_type == "settle_invoice":
            settle_commissions_invoice_line = self.env["settle.commissions.invoice.line"]
            select_invoice_lines = self.invoice_lines.filtered(lambda l: l.selected)
            
            for line in select_invoice_lines:
                if self.target_type == 'user_id':
                    line.invoice_id.is_settle_commission_salesperson = True
                if self.target_type == 'sale_spec':
                    line.invoice_id.is_settle_commission_sale_spec = True
                if self.target_type == 'sale_manager_id':
                    line.invoice_id.is_settle_commission_sale_manager = True
                    
                settle_commissions_invoice_line.create({
                    'settle_commissions_id':settle_commissions_id,
                    'invoice_id': line.invoice_id.id,
                    'invoice_id_date': line.invoice_id_date,
                    'form_no': line.form_no,
                    'partner_id': line.partner_id.id,
                    'product_id': line.product_id.id,
                    'total_amount_tax': line.total_amount_tax,
                    'total_amount_untax': line.total_amount_untax,
                    'note': line.note,
                    })
                
        action = {
            'name': 'Settle Commissions',
            'type': 'ir.actions.act_window',
            'res_model': 'settle.commissions',
            'res_id': settle_commissions_id, 'view_mode': 'form',
            }
        return action

class GenerateSettleCommissionsPaymentLine(models.Model):
    _name = "generate.settle.commissions.payment.line"
    _description = "Generate Settle Commissions Payment Line"

    generate_settle_commissions_id = fields.Many2one('generate.settle.commissions', string = 'Generate Settle Commissions')
    selected = fields.Boolean(string="Select")
    payment_id = fields.Many2one('account.payment', string='PDC No.')
    payment_id_create_date = fields.Date(string = "Create PDC")
    payment_id_date = fields.Date(string = "Date Rec.")
    invoice_id = fields.Many2one('account.move', string='Invoice')
    invoice_id_date = fields.Date(string = "INV Date")
    form_no = fields.Char(string="SPE Invoice")
    partner_id = fields.Many2one('res.partner', string = 'ลูกค้า')
    product_id = fields.Many2one('product.product', string='สินค้า')
    total_amount_tax = fields.Float(string = "รับ-รวมภาษี")
    total_amount_untax = fields.Float(string = "รับ-ก่อนภาษี")
    note = fields.Text('หมายเหตุ')

class GenerateSettleCommissionsInvoiceLine(models.Model):
    _name = "generate.settle.commissions.invoice.line"
    _description = "Generate Settle Commissions Invoice Line"

    generate_settle_commissions_id = fields.Many2one('generate.settle.commissions', string = 'Generate Settle Commissions')
    selected = fields.Boolean(string="Select")
    invoice_id = fields.Many2one('account.move', string='Invoice')
    invoice_id_date = fields.Date(string = "INV Date")
    form_no = fields.Char(string="SPE Invoice")
    partner_id = fields.Many2one('res.partner', string = 'ลูกค้า')
    product_id = fields.Many2one('product.product', string='สินค้า')
    total_amount_tax = fields.Float(string = "รับ-รวมภาษี")
    total_amount_untax = fields.Float(string = "รับ-ก่อนภาษี")
    note = fields.Text('หมายเหตุ')