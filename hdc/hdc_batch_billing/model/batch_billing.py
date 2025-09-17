# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo import models, fields, api
from datetime import date

class BatchBilling(models.Model):
    _name = 'batch.billing'
    _description = 'Batch Billing'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft',tracking=True)

    name = fields.Char(string='Batch Billing No.', default="/", readonly=True, copy=False, tracking=True)
    responsible_id = fields.Many2one('res.users', string='Responsible',tracking=True,default=lambda self: self.env.user)
    billing_route_id = fields.Many2one('account.billing.route', string='Billing Route',tracking=True)
    description = fields.Char(string='Description',tracking=True)
    date = fields.Date(string='Date',tracking=True)
    payment_credit = fields.Selection([('cash', 'Cash'), ('credit', 'Credit')], string='Payment Credit',tracking=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.company)

    notes = fields.Text(string='Notes')
    # One2many relation with batch.billing.line
    line_ids = fields.One2many('batch.billing.line', 'batch_billing_id', 
        string='Billing Lines',)
    
    finance_receipt = fields.Boolean(default=False, string="Finance Receipt",tracking=True)
    finance_date = fields.Date(string='Finance Date',tracking=True)
    finance_receipt_by = fields.Many2one('res.users', string='Finance Receipt By',tracking=True)
    
    def action_confirm(self):
        self.state = 'confirm'

    def action_validate(self):
        for record in self:
            company_id = record.company_id
            if company_id:
                self_comp = record.with_company(company_id)
                self.name = self_comp.env['ir.sequence'].next_by_code("batch.billing") or False
            record.state = 'done'
            
            line_ids = record.line_ids
            if line_ids:
                for line in line_ids:
                    if line.invoice_id.billing_ids:
                        line.invoice_id.billing_ids.write({
                            'batch_billing_no': self.name,
                            'batch_billing_status': 'done'
                        })


    def action_cancel(self):
        self.state = 'cancelled'

    def action_reset_to_draft(self):
        for record in self:
            record.write({
                'state': 'draft',
                'finance_receipt': True,
                'finance_date': date.today(),
                'finance_receipt_by': self.env.user.id,
            })
            line_ids = record.line_ids
            if line_ids:
                for line in line_ids:
                    if line.invoice_id.billing_ids:
                        # ปรับ batch_billing_status เป็น wait
                        line.invoice_id.billing_ids.write({
                            'batch_billing_status': 'wait'
                        })

                
    
    def action_add_billing(self):
        return {
            'name': 'Add Billing',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.add.billing',
            'view_mode': 'form',
            # 'view_id': self.env.ref('hdc_batch_billing.add_billing_wizard_action').id,
            'target': 'new',
            "context": {"default_batch_billing_id": self.id,
                        "default_company_id": self.company_id.id
                        },
        }
    
    def action_add_invoice_line(self):
        return {
            'name': 'Add Invoice Line',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.add.invoice.line',
            'view_mode': 'form',
            # 'view_id': self.env.ref('hdc_batch_billing.add_billing_wizard_action').id,
            'target': 'new',
            "context": {"default_batch_billing_id": self.id,
                        "default_company_id": self.company_id.id
                        },
        }
    
    def action_finance_receipt(self):
        for record in self:
            record.write({
                'finance_receipt': True,
                'finance_date': date.today(),
                'finance_receipt_by': self.env.user.id,
            })


    @api.model
    def create(self, values):
        values["name"] = self.env["ir.sequence"].next_by_code("batch.billing")
        res = super(BatchBilling, self).create(values)
        return res
    
    invoice_exclude_ids = fields.Many2many(
        'account.move',
        string='Excluded Invoices',
        compute='_compute_invoice_exclude_ids',
        store=False,
    )

    @api.depends('line_ids.invoice_id')
    def _compute_invoice_exclude_ids(self):
        for line in self:
            if line.line_ids:
                # ดึง Invoices ที่ถูกเลือกใน batch_billing_id ปัจจุบัน
                selected_invoices = line.line_ids.mapped('invoice_id.id')
                line.invoice_exclude_ids = [(6, 0, selected_invoices)]
            else:
                line.invoice_exclude_ids = [(6, 0, [])]

    def action_finance_check_all(self):
        for record in self:
            if record.line_ids:
                record.line_ids.write({'finance_check': True})

class BatchBillingLine(models.Model):
    _name = 'batch.billing.line'
    _description = 'Batch Billing Line'

    batch_billing_id = fields.Many2one('batch.billing', string='Batch Billing Reference', required=True, ondelete='cascade')
    batch_billing_route_id = fields.Many2one(related="batch_billing_id.billing_route_id",store=True,)

    
    invoice_exclude_ids = fields.Many2many(
        related='batch_billing_id.invoice_exclude_ids',
    )

    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice No.',
        domain="[('move_type', 'in', ['out_invoice', 'out_refund']), "
               "('state', '=', 'posted'), "
               "('payment_state', 'in', ['not_paid', 'partial']), "
               "('id', 'not in', invoice_exclude_ids)]"
    )

    invoice_date = fields.Date(string='Invoice Date',related='invoice_id.invoice_date')

    company_currency_id = fields.Many2one(string='Company Currency', readonly=True,
        related='batch_billing_id.company_id.currency_id')

    partner_id = fields.Many2one('res.partner', string='Partner',related='invoice_id.partner_id')
    # billing_no = fields.Char(string='Billing No.',related='invoice_id.name')
    billing_no = fields.Char(string='Billing No.')
    due_date = fields.Date(string='Due Date',related='invoice_id.invoice_date_due_payment_term')
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Term',related='invoice_id.invoice_payment_term_id')
    origin = fields.Char(string='Origin',related='invoice_id.invoice_origin')
    billing_route_id = fields.Many2one('account.billing.route', string='Billing Route',related='invoice_id.billing_route_id')
    amount = fields.Monetary(string='Amount',related='invoice_id.amount_total_signed', currency_field="company_currency_id")
    amount_due = fields.Monetary(string='Amount Due',related='invoice_id.amount_residual', currency_field="company_currency_id")

    finance_check = fields.Boolean(default=False, string="Finance Check")

    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        for move in self:
            if move.invoice_id.form_no:
                move.billing_no = move.invoice_id.form_no
            else:
                move.billing_no = move.invoice_id.name

    status = fields.Selection(
        related="invoice_id.state",
        store=True,
        string='Status'
    )
    payment_status = fields.Selection(
        related="invoice_id.payment_state",
        store=True,
        string='Payment Status'
    )
