# -*- coding: utf-8 -*-
from lxml import etree
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

class GenerateSettleCommissionsMall(models.Model):
    _name = "generate.settle.commissions.mall"
    _description = "Generate Settle Commissions Mall"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Generate Settle Commissions Mall", readonly=True, default='Generate Settle Commissions Mall')
    team_id = fields.Many2one('crm.team', string = 'Sales Team')
    user_id = fields.Many2one('res.users', string = 'Salesperson', domain="[('id', 'in', member_ids)]")
    sale_spec = fields.Many2one('res.users', string = 'Sale Spec', domain="[('id', 'in', spec_member_ids)]")
    sale_manager_id = fields.Many2one("res.users", string = "Sale Manager", domain="[('id', '=', manager_member_id)]")
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

    receipted_date_form = fields.Date(string = "Receipted Date")
    receipted_date_to = fields.Date(string = "Receipted Date To")
    invoice_date_form = fields.Date(string = "Invoice Date")
    invoice_date_to = fields.Date(string = "Invoice Date To")

    selected = fields.Boolean(string = "Select All")
    payment_lines = fields.One2many('generate.settle.commissions.mall.payment.line', 'generate_settle_commissions_mall_id', string = 'Payment Lines')
    invoice_lines = fields.One2many('generate.settle.commissions.mall.invoice.line', 'generate_settle_commissions_mall_id', string = 'Invoice Lines')

    @api.onchange('target_type')
    def _target_type_onchange(self):
        self.clear_all_action()

    @api.onchange('selected')
    def _selected_onchange(self):
        if self.selected:
            if self.target_type == "normal":
                for line in self.payment_lines:
                    line.selected = True
            elif self.target_type == "sold_out":
                for line in self.invoice_lines:
                    line.selected = True
        else:
            if self.target_type == "normal":
                for line in self.payment_lines:
                    line.selected = False
            elif self.target_type == "sold_out":
                for line in self.invoice_lines:
                    line.selected = False

    @api.onchange('team_id')
    def _team_id_onchange(self):
        self.sale_manager_id = self.team_id.user_id.id
        domain_user_id = [('id', 'in', self.team_id.member_ids.ids)]
        domain_sale_manager_id = [('id', '=', self.team_id.user_id.id)]
        domain_sale_spec = [('id', 'in', self.team_id.sale_spec_member_ids.ids)]
        return {'domain': {'user_id': domain_user_id,'sale_manager_id':domain_sale_manager_id,'sale_spec':domain_sale_spec}}
    
    def search_action(self):
        user_company = self.env.context['allowed_company_ids']
        all_company = self.env['res.company'].search([])

        if len(user_company) < len(all_company):
            raise UserError('Not Allow Please Change to Multi Companies')
        
        self.payment_lines = False
        self.invoice_lines = False
        self.selected = False
        domain_search = [('state', '=', 'posted'),('is_settle_commission_mall', '=',False)]
        if self.target_type_commission == 'user_id':
            domain_search += [('is_settle_commission_mall_salesperson', '=',False)]
        if self.target_type_commission == 'sale_spec':
            domain_search += [('is_settle_commission_mall_sale_spec', '=',False)]
        if self.target_type_commission == 'sale_manager_id':
            domain_search += [('is_settle_commission_mall_sale_manager', '=',False)]

        if self.target_type == "normal":
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

                        if self.user_id and self.target_type_commission == 'user_id':
                            if invoice.invoice_user_id != self.user_id:
                                check_user_id = False

                        if self.sale_spec and self.target_type_commission == 'sale_spec':
                            if invoice.sale_spec != self.sale_spec:
                                check_sale_spec = False
                        
                        if self.sale_manager_id and self.target_type_commission == 'sale_manager_id':
                            if invoice.team_id.user_id != self.sale_manager_id:
                                check_sale_manager_id = False

                        if check_invoice_date and check_team_id and check_user_id and check_sale_spec and check_sale_manager_id:
                            for invoice_line in invoice.invoice_line_ids:
                                if invoice_line.product_id.type != 'service':
                                    total_amount_tax = invoice_line.price_total
                                    total_amount_untax = invoice_line.price_subtotal
                                            
                                    line = (0, 0, {
                                        'generate_settle_commissions_mall_id': self.id,
                                        'payment_id': payment.id,
                                        'payment_id_create_date': payment.create_date.date(),
                                        'payment_id_date': payment.date,
                                        'invoice_id': invoice.id,
                                        'invoice_id_date': invoice.invoice_date,
                                        'form_no': invoice.form_no,
                                        'partner_id': invoice.partner_id.id,
                                        'company_id':payment.company_id.id,
                                        'product_id': invoice_line.product_id.id,
                                        'total_amount_tax': total_amount_tax,
                                        'total_amount_untax': total_amount_untax,
                                    })
                                    order_line.append(line)

            self.write({
                'payment_lines': order_line
            })
        elif self.target_type == "sold_out":
            domain_search += [('move_type', '=', 'out_refund')]
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

                if self.user_id and self.target_type_commission == 'user_id':
                    if invoice.invoice_user_id != self.user_id:
                        check_user_id = False

                if self.sale_spec and self.target_type_commission == 'sale_spec':
                    if invoice.sale_spec != self.sale_spec:
                        check_sale_spec = False
                
                if self.sale_manager_id and self.target_type_commission == 'sale_manager_id':
                    if invoice.team_id.user_id != self.sale_manager_id:
                        check_sale_manager_id = False

                if check_invoice_date and check_team_id and check_user_id and check_sale_spec and check_sale_manager_id:
                    for invoice_line in invoice.invoice_line_ids:
                        if invoice_line.product_id.type != 'service':
                            total_amount_tax = invoice_line.price_total
                            total_amount_untax = invoice_line.price_subtotal
                                    
                            line = (0, 0, {
                                'generate_settle_commissions_mall_id': self.id,
                                'invoice_id': invoice.id,
                                'invoice_id_date': invoice.invoice_date,
                                'form_no': invoice.form_no,
                                'partner_id': invoice.partner_id.id,
                                'company_id':invoice.company_id.id,
                                'product_id': invoice_line.product_id.id,
                                'total_amount_tax': total_amount_tax,
                                'total_amount_untax': total_amount_untax,
                            })
                            order_line.append(line)

            self.write({
                'invoice_lines': order_line
            })

    def clear_all_action(self):
        self.receipted_date_form = False
        self.receipted_date_to = False
        self.invoice_date_form = False
        self.invoice_date_to = False
        self.payment_lines = False
        self.invoice_lines = False
        self.selected = False

    def check_commission_lines_partner(self,commission_lines_data,partner_id,company_id):
        check_partner = False
        check_company = False
        for item in commission_lines_data:
            if item['partner_id'] == partner_id.id:
                check_partner = True
                if item['company_id'] == company_id.id:
                    check_company = True
        return check_partner,check_company
    
    def sort_partner_id(self,e):
        return e['partner_id_name']
    
    def create_settlements(self):
        user_company = self.env.context['allowed_company_ids']
        all_company = self.env['res.company'].search([])

        if len(user_company) < len(all_company):
            raise UserError('Not Allow Please Change to Multi Companies')
        
        return {
                'name': _('Make Settlements Mall?'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'wizard.create.settlements.mall',
                'view_mode': 'form',
                'target': 'new',
                'context': {"default_generate_settle_commissions_mall_id": self.id,
                            "default_team_id": self.team_id.id,
                            "default_user_id": self.user_id.id,
                            "default_sale_spec": self.sale_spec.id,
                            "default_sale_manager_id": self.sale_manager_id.id,
                            "default_target_type": self.target_type,
                            "default_target_type_commission": self.target_type_commission,},
            }
    
    def create_new_settlements(self):
        payment_lines = []
        invoice_lines = []
        commission_lines_data = []
        commission_lines = []
        commission_sold_out_lines_data = []
        commission_sold_out_lines = []
        if self.target_type == "normal":
            select_payment_lines = self.payment_lines.filtered(lambda l: l.selected)
            payment_id_old = False
            payment_id_current = False
            for line in select_payment_lines:
                line.payment_id.is_settle_commission_mall = True
                payment_id_current = line.payment_id.id
                payment_lines.append((0, 0, {
                    'payment_id': line.payment_id.id,
                    'payment_id_create_date': line.payment_id_create_date,
                    'payment_id_date': line.payment_id_date,
                    'invoice_id': line.invoice_id.id,
                    'invoice_id_date': line.invoice_id_date,
                    'form_no': line.form_no,
                    'partner_id': line.partner_id.id,
                    'company_id':line.company_id.id,
                    'product_id': line.product_id.id,
                    'total_amount_tax': line.total_amount_tax,
                    'total_amount_untax': line.total_amount_untax,
                    'note': line.note,
                    }))
                
                check_partner,check_company = self.check_commission_lines_partner(commission_lines_data,line.partner_id,line.company_id)
                
                if check_partner and check_company and payment_id_current == payment_id_old:
                    for item in commission_lines_data:
                        if item['partner_id'] == line.partner_id.id and item['company_id'] == line.company_id.id:
                            total_amount_tax = item['total_amount_tax'] + line.total_amount_tax
                            item['total_amount_tax'] = total_amount_tax
                            total_amount_untax = item['total_amount_untax'] + line.total_amount_untax
                            item['total_amount_untax'] = total_amount_untax
                else:
                    commission_lines_data.append({
                    'payment_id': line.payment_id.id,
                    'payment_id_date': line.payment_id_date,
                    'company_id':line.company_id.id,
                    'partner_id': line.partner_id.id,
                    'partner_id_name': line.partner_id.name,
                    'total_amount_tax': line.total_amount_tax,
                    'total_amount_untax': line.total_amount_untax,
                    'note': line.note,
                    })
                
                payment_id_old = payment_id_current

            commission_lines_data.sort(key=self.sort_partner_id)
            for item in commission_lines_data:
                commission_lines.append((0, 0, {
                    'payment_id': item['payment_id'],
                    'payment_id_date': item['payment_id_date'],
                    'company_id': item['company_id'],
                    'partner_id': item['partner_id'],
                    'total_amount_tax': item['total_amount_tax'],
                    'total_amount_untax': item['total_amount_untax'],
                    'note': item['note'],
                    }))

        elif self.target_type == "sold_out":
            select_invoice_lines = self.invoice_lines.filtered(lambda l: l.selected)
            for line in select_invoice_lines:
                line.invoice_id.is_settle_commission_mall = True

                invoice_lines.append((0, 0, {
                    'invoice_id': line.invoice_id.id,
                    'invoice_id_date': line.invoice_id_date,
                    'form_no': line.form_no,
                    'partner_id': line.partner_id.id,
                    'company_id':line.company_id.id,
                    'product_id': line.product_id.id,
                    'total_amount_tax': line.total_amount_tax,
                    'total_amount_untax': line.total_amount_untax,
                    'note': line.note,
                    }))
                
                check_partner,check_company = self.check_commission_lines_partner(commission_sold_out_lines_data,line.partner_id,line.company_id)
                if check_partner and check_company:
                    for item in commission_sold_out_lines_data:
                        if item['partner_id'] == line.partner_id.id and item['company_id'] == line.company_id.id:
                            total_amount_untax_cn = item['total_amount_untax_cn'] + line.total_amount_untax
                            item['total_amount_untax_cn'] = total_amount_untax_cn
                else:
                    commission_sold_out_lines_data.append({
                    'partner_id': line.partner_id.id,
                    'partner_id_name': line.partner_id.name,
                    'company_id':line.company_id.id,
                    'total_amount_untax_cn': line.total_amount_untax,
                    })
            commission_sold_out_lines_data.sort(key=self.sort_partner_id)
            for item in commission_sold_out_lines_data:
                commission_sold_out_lines.append((0, 0, {
                    'partner_id': item['partner_id'],
                    'company_id':item['company_id'],
                    'total_amount_untax_cn': item['total_amount_untax_cn'],
                    }))

        commission_date = datetime.now()

        user_id = False
        sale_spec = False
        sale_manager_id = False

        if self.target_type_commission == 'user_id':
            user_id = self.user_id.id
        if self.target_type_commission == 'sale_spec':
            sale_spec = self.sale_spec.id
        if self.target_type_commission == 'sale_manager_id':
            sale_manager_id = self.sale_manager_id.id
        
        settle_commission_mall = {
            'target_type':self.target_type,
            'team_id': self.team_id.id, 
            'target_type_commission':self.target_type_commission,
            'user_id': user_id,
            'sale_spec': sale_spec, 
            'sale_manager_id': sale_manager_id,
            'commission_date': commission_date,
            'receipted_date_form': self.receipted_date_form, 
            'receipted_date_to': self.receipted_date_to,
            'invoice_date_form': self.invoice_date_form, 
            'invoice_date_to': self.invoice_date_to,
            'commission_lines': commission_lines,
            'payment_lines': payment_lines,
            'commission_sold_out_lines': commission_sold_out_lines,
            'invoice_lines': invoice_lines,
            }

        settle_commission_mall_id = self.env['settle.commissions.mall'].create(settle_commission_mall)
        action = {
            'name': 'Settle Commissions Mall',
            'type': 'ir.actions.act_window',
            'res_model': 'settle.commissions.mall',
            'res_id': settle_commission_mall_id.id, 'view_mode': 'form',
            }
        return action
    
    def add_to_settlements(self,settle_commissions_mall_id=None):
        commission_lines_data = []
        commission_sold_out_lines_data = []

        settle_commissions_mall = self.env['settle.commissions.mall'].search([('id','=',settle_commissions_mall_id)])
        
        if self.target_type == "normal":
            settle_commissions_mall_payment_line = self.env["settle.commissions.mall.payment.line"]
            select_payment_lines = self.payment_lines.filtered(lambda l: l.selected)
            payment_id_old = False
            payment_id_current = False

            for line in select_payment_lines:
                line.payment_id.is_settle_commission_mall = True
                settle_commissions_mall_payment_line.create({
                    'settle_commissions_mall_id': settle_commissions_mall_id,
                    'payment_id': line.payment_id.id,
                    'payment_id_create_date': line.payment_id_create_date,
                    'payment_id_date': line.payment_id_date,
                    'invoice_id': line.invoice_id.id,
                    'invoice_id_date': line.invoice_id_date,
                    'form_no': line.form_no,
                    'partner_id': line.partner_id.id,
                    'company_id':line.company_id.id,
                    'product_id': line.product_id.id,
                    'total_amount_tax': line.total_amount_tax,
                    'total_amount_untax': line.total_amount_untax,
                    'note': line.note,
                    })

            for line2 in settle_commissions_mall.payment_lines:
                check_partner,check_company = self.check_commission_lines_partner(commission_lines_data,line2.partner_id,line2.company_id)
                payment_id_current = line2.payment_id.id
                if check_partner and check_company and payment_id_current == payment_id_old:
                    for item in commission_lines_data:
                        if item['partner_id'] == line2.partner_id.id and item['company_id'] == line2.company_id.id:
                            total_amount_tax = item['total_amount_tax'] + line2.total_amount_tax
                            item['total_amount_tax'] = total_amount_tax
                            total_amount_untax = item['total_amount_untax'] + line2.total_amount_untax
                            item['total_amount_untax'] = total_amount_untax
                else:
                    commission_lines_data.append({
                    'payment_id': line2.payment_id.id,
                    'payment_id_date': line2.payment_id_date,
                    'company_id':line2.company_id.id,
                    'partner_id': line2.partner_id.id,
                    'partner_id_name': line2.partner_id.name,
                    'total_amount_tax': line2.total_amount_tax,
                    'total_amount_untax': line2.total_amount_untax,
                    'note': line2.note,
                    })
                
                payment_id_old = payment_id_current

            for line3 in settle_commissions_mall.commission_lines:
                line3.unlink()

            commission_lines_data.sort(key=self.sort_partner_id)
            commission_lines = self.env["settle.commissions.mall.line"]

            for item in commission_lines_data:
                commission_lines.create({
                    'settle_commissions_mall_id': settle_commissions_mall_id,
                    'payment_id': item['payment_id'],
                    'payment_id_date': item['payment_id_date'],
                    'company_id': item['company_id'],
                    'partner_id': item['partner_id'],
                    'total_amount_tax': item['total_amount_tax'],
                    'total_amount_untax': item['total_amount_untax'],
                    'note': item['note'],
                    })

        elif self.target_type == "sold_out":
            settle_commissions_mall_invoice_line = self.env["settle.commissions.mall.invoice.line"]
            select_invoice_lines = self.invoice_lines.filtered(lambda l: l.selected)
            
            for line in select_invoice_lines:
                line.invoice_id.is_settle_commission_mall = True
                settle_commissions_mall_invoice_line.create({
                    'settle_commissions_mall_id': settle_commissions_mall_id,
                    'invoice_id': line.invoice_id.id,
                    'invoice_id_date': line.invoice_id_date,
                    'form_no': line.form_no,
                    'partner_id': line.partner_id.id,
                    'company_id':line.company_id.id,
                    'product_id': line.product_id.id,
                    'total_amount_tax': line.total_amount_tax,
                    'total_amount_untax': line.total_amount_untax,
                    'note': line.note,
                    })
                
            for line2 in settle_commissions_mall.invoice_lines:
                check_partner,check_company = self.check_commission_lines_partner(commission_sold_out_lines_data,line2.partner_id,line2.company_id)
                if check_partner and check_company:
                    for item in commission_sold_out_lines_data:
                        if item['partner_id'] == line2.partner_id.id and item['company_id'] == line2.company_id.id:
                            total_amount_untax_cn = item['total_amount_untax_cn'] + line2.total_amount_untax
                            item['total_amount_untax_cn'] = total_amount_untax_cn
                else:
                    commission_sold_out_lines_data.append({
                    'partner_id': line2.partner_id.id,
                    'partner_id_name': line2.partner_id.name,
                    'company_id':line2.company_id.id,
                    'total_amount_untax_cn': line2.total_amount_untax,
                    })
            
            for line3 in settle_commissions_mall.commission_sold_out_lines:
                line3.unlink()

            commission_sold_out_lines_data.sort(key=self.sort_partner_id)
            commission_sold_out_lines = self.env["settle.commissions.mall.sold.out.line"]
            
            for item in commission_sold_out_lines_data:
                commission_sold_out_lines.create({
                    'settle_commissions_mall_id': settle_commissions_mall_id,
                    'partner_id': item['partner_id'],
                    'company_id':item['company_id'],
                    'total_amount_untax_cn': item['total_amount_untax_cn'],
                    })

        action = {
            'name': 'Settle Commissions Mall',
            'type': 'ir.actions.act_window',
            'res_model': 'settle.commissions.mall',
            'res_id': settle_commissions_mall_id, 'view_mode': 'form',
            }
        return action

class GenerateSettleCommissionsMallPaymentLine(models.Model):
    _name = "generate.settle.commissions.mall.payment.line"
    _description = "Generate Settle Commissions Mall Payment Line"

    generate_settle_commissions_mall_id = fields.Many2one('generate.settle.commissions.mall', string = 'Generate Settle Commissions')
    selected = fields.Boolean(string="Select")
    payment_id = fields.Many2one('account.payment', string='PDC No.')
    payment_id_create_date = fields.Date(string = "Create PDC")
    payment_id_date = fields.Date(string = "Date Rec.")
    invoice_id = fields.Many2one('account.move', string='Invoice')
    invoice_id_date = fields.Date(string = "INV Date")
    form_no = fields.Char(string="SPE Invoice")
    partner_id = fields.Many2one('res.partner', string = 'ลูกค้า')
    company_id = fields.Many2one('res.company', string='Company')
    product_id = fields.Many2one('product.product', string='สินค้า')
    total_amount_tax = fields.Float(string = "รับ-รวมภาษี")
    total_amount_untax = fields.Float(string = "รับ-ก่อนภาษี")
    note = fields.Text('หมายเหตุ')

class GenerateSettleCommissionsMallInvoiceLine(models.Model):
    _name = "generate.settle.commissions.mall.invoice.line"
    _description = "Generate Settle Commissions Mall Invoice Line"

    generate_settle_commissions_mall_id = fields.Many2one('generate.settle.commissions.mall', string = 'Generate Settle Commissions')
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