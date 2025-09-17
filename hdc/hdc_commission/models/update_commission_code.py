# -*- coding: utf-8 -*-
from lxml import etree
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

class UpdateCommissionCode(models.TransientModel):
    _name = "update.commission.code"
    _description = "Update Commission Code"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Update Commission Code", readonly=True, default='Update Commission Code')
    team_id = fields.Many2one('crm.team', string = 'Sales Team')
    invoice_user_employee_id = fields.Many2one('hr.employee', string = 'Salesperson', index = True, tracking = True,domain="[('id', 'in', sale_employee_ids)]")
    sale_spec_employee = fields.Many2one('hr.employee', string = 'Sale Spec',domain="[('id', 'in', sale_spec_employee_ids)]")
    sale_manager_employee_id = fields.Many2one('hr.employee', string = "Sale Manager", domain="[('id', '=', manager_member_id)]")
    target_type = fields.Selection([
        ('sale_person', 'Salesperson'),
        ('sale_spec', 'Sale Spec'),
        ('sale_manager', 'Sale Manager or Sales Team'),
    ], string="Commission Target",default='sale_manager')

    @api.depends('team_id')
    def _compute_sale_employee_ids(self):
        for rec in self:
            rec.sale_employee_ids = rec.team_id.sale_employee_ids.ids

    sale_employee_ids = fields.Many2many('hr.employee', compute = "_compute_sale_employee_ids")

    @api.depends('team_id')
    def _compute_sale_spec_employee_ids(self):
        for rec in self:
            rec.sale_spec_employee_ids = rec.team_id.sale_spec_employee_ids.ids

    sale_spec_employee_ids = fields.Many2many('hr.employee', compute = "_compute_sale_spec_employee_ids")

    @api.depends('team_id')
    def _compute_manager_member_ids(self):
        for rec in self:
            rec.manager_member_id = rec.team_id.user_employee_id.id
    manager_member_id = fields.Many2one('hr.employee', compute = "_compute_manager_member_ids")

    invoice_date_form = fields.Date(string = "Invoice Date")
    invoice_date_to = fields.Date(string = "Invoice Date To")

    selected = fields.Boolean(string = "Select All")
    invoice_lines = fields.One2many('update.commission.code.invoice.line', 'update_commission_code_id', string = 'Invoice Lines')

    partner_ids = fields.Many2many('res.partner',string="Customer", 
        domain=lambda self: [
            ('customer', '=', True),
        ])
    invoice_search_type = fields.Selection([
        ('invoice', 'Invoice No'),
        ('spe_invoice', 'SPE Invoice'),
    ], string="Invoice Search From",default='invoice')

    invoice_ids = fields.Many2many('account.move',string="Invoices No", 
        domain=lambda self: [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
        ])
        
    @api.onchange('invoice_search_type')
    def _onchange_invoice_search_type(self):
        self.invoice_ids = False
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
        ]
        if self.invoice_search_type == 'spe_invoice':
            domain.append(('form_no', '!=', False))
        return {'domain': {'invoice_ids': domain}}
    
    @api.onchange('team_id')
    def _team_id_onchange(self):
        self.sale_manager_employee_id = self.team_id.user_employee_id.id
        domain_invoice_user_employee_id = [('id', 'in', self.team_id.sale_employee_ids.ids)]
        domain_sale_manager_employee_id = [('id', '=', self.team_id.user_employee_id.id)]
        domain_sale_spec_employee = [('id', 'in', self.team_id.sale_spec_employee_ids.ids)]
        return {'domain': {'invoice_user_employee_id': domain_invoice_user_employee_id,'sale_manager_employee_id':domain_sale_manager_employee_id,'sale_spec_employee':domain_sale_spec_employee}}
    
    @api.onchange('selected')
    def _selected_onchange(self):
        if self.selected:
            for line in self.invoice_lines:
                line.selected = True
        else:
            for line in self.invoice_lines:
                line.selected = False

    def search_action(self):
        user_company = self.env.context['allowed_company_ids']
        all_company = self.env['res.company'].search([])

        if len(user_company) < len(all_company):
            raise UserError('Not Allow Please Change to Multi Companies')
        
        self.invoice_lines = False
        self.selected = False
        domain_search = [('state', '=', 'posted'),('move_type', '=', 'out_invoice'),
                         ('is_settle_commission_salesperson', '=', False),
                         ('is_settle_commission_sale_spec', '=', False),
                         ('is_settle_commission_sale_manager', '=', False),
                         ('is_settle_commission_mall', '=', False),
                         ('is_settle_commission_mall_salesperson', '=', False),
                         ('is_settle_commission_mall_sale_spec', '=', False),
                         ('is_settle_commission_mall_sale_manager', '=', False),]
        if len(self.invoice_ids) > 0:
            domain_search += [('id', 'in',self.invoice_ids.ids)]
        if len(self.partner_ids) > 0:
            domain_search += [('partner_id', 'in', self.partner_ids.ids)]
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

            if self.invoice_user_employee_id and self.target_type == 'sale_person':
                if invoice.invoice_user_employee_id != self.invoice_user_employee_id:
                    check_user_id = False

            if self.sale_spec_employee and self.target_type == 'sale_spec':
                if invoice.sale_spec_employee != self.sale_spec_employee:
                    check_sale_spec = False
            
            if self.sale_manager_employee_id and self.target_type == 'sale_manager':
                if invoice.sale_manager_employee_id != self.sale_manager_employee_id:
                    check_sale_manager_id = False

            if check_invoice_date and check_team_id and check_user_id and check_sale_spec and check_sale_manager_id:
                for invoice_line in invoice.invoice_line_ids:
                    if invoice_line.product_id.type != 'service':
                                
                        line = (0, 0, {
                            'update_commission_code_id': self.id,
                            'commission_code': invoice_line.commission_code.ids,
                            'invoice_id': invoice.id,
                            'invoice_line_id': invoice_line.id,
                            'invoice_id_date': invoice.invoice_date,
                            'form_no': invoice.form_no,
                            'partner_id': invoice.partner_id.id,
                            'product_id': invoice_line.product_id.id,
                            'quantity': invoice_line.quantity,
                            'product_uom_id': invoice_line.product_uom_id.id,
                            'price_unit': invoice_line.price_unit,
                            'triple_discount': invoice_line.triple_discount,
                            'price_subtotal': invoice_line.price_subtotal,
                            'currency_id': invoice_line.currency_id.id,
                        })
                        order_line.append(line)

        self.write({
            'invoice_lines': order_line
        })

    def clear_all_action(self):
        self.team_id = False
        self.invoice_user_employee_id = False
        self.sale_spec_employee = False
        self.sale_manager_employee_id = False

        self.invoice_date_form = False
        self.invoice_date_to = False
        self.invoice_lines = False
        self.selected = False
        self.partner_ids = False
        self.invoice_ids = False

    def wizard_update_commission_code(self):
        user_company = self.env.context['allowed_company_ids']
        all_company = self.env['res.company'].search([])

        if len(user_company) < len(all_company):
            raise UserError('Not Allow Please Change to Multi Companies')
        
        order_line = []
        for invoice_line in self.invoice_lines:
            if invoice_line.selected == True:    
                line = (0, 0, {
                    'selected': invoice_line.selected,
                    'commission_code': invoice_line.commission_code.ids,
                    'invoice_id': invoice_line.invoice_id.id,
                    'invoice_line_id': invoice_line.invoice_line_id.id,
                    'invoice_id_date': invoice_line.invoice_id_date,
                    'form_no': invoice_line.form_no,
                    'partner_id': invoice_line.partner_id.id,
                    'product_id': invoice_line.product_id.id,
                    'quantity': invoice_line.quantity,
                    'product_uom_id': invoice_line.product_uom_id.id,
                    'price_unit': invoice_line.price_unit,
                    'triple_discount': invoice_line.triple_discount,
                    'price_subtotal': invoice_line.price_subtotal,
                    'currency_id': invoice_line.currency_id.id,
                })
                order_line.append(line)
        return {
                'name': _('Update Commission Code'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'wizard.update.commission.code',
                'view_mode': 'form',
                'target': 'new',
                'context': {"default_update_commission_code_id": self.id,
                            "default_invoice_lines": order_line,},
            }

class UpdateCommissionCodeInvoiceLine(models.TransientModel):
    _name = "update.commission.code.invoice.line"
    _description = "Update Commission Code Invoice Line"

    update_commission_code_id = fields.Many2one('update.commission.code', string = 'Update Commission Code')
    selected = fields.Boolean(string="Select")
    commission_code = fields.Many2many('commission.type', string = 'Commission Code')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    invoice_line_id = fields.Many2one('account.move.line', string='Invoice Line')
    invoice_id_date = fields.Date(string = "INV Date")
    form_no = fields.Char(string="SPE Invoice")
    partner_id = fields.Many2one('res.partner', string = 'ลูกค้า')
    product_id = fields.Many2one('product.product', string='สินค้า')
    quantity = fields.Float(string='Quantity',)
    product_uom_id = fields.Many2one('uom.uom', string='UOM')
    price_unit = fields.Float(string='Price',digits='Product Price')
    triple_discount = fields.Char('Discount',)
    price_subtotal = fields.Monetary(string='Subtotal', store=True, readonly=True,currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency')