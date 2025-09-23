# -*- encoding: utf-8 -*-
from odoo import api, fields, models

class BatchBillingLine(models.Model):
    _inherit = 'batch.billing.line'
    _rec_name = 'display_name'
    
    @api.depends('batch_billing_id', 'batch_billing_id.name')
    def _compute_display_name(self):
        for line in self:
            line.display_name = f"{line.batch_billing_id.name} - {line.partner_id.name} - {line.billing_no}"
                
    billing_date = fields.Date(string='Billing Date', compute='_compute_billing_info', store=True)
    billing_due_date = fields.Date(string='Billing Due Date', compute='_compute_billing_info', store=True)
    billing_receipt_date = fields.Date(string='Billing Receipt Date', compute='_compute_billing_info', store=True)
    spe_invoice = fields.Boolean(string='SPE Invoice', compute='_compute_billing_info', store=True)
    due_payment = fields.Date(string='Due Payment', compute='_compute_billing_info', store=True)
    payment_period = fields.Many2one('account.payment.period', string='Payment Period', compute='_compute_billing_info', store=True)
    done_job = fields.Boolean(string='Done Job', compute='_compute_messenger_done_job', store=True)
    messenger_job_id = fields.Many2one('messenger.job', string='Messenger Job No.', ondelete='cascade', readonly=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    
    @api.depends('invoice_id')
    def _compute_billing_info(self):
        for line in self:
            line.due_payment = line.invoice_id.due_payment
            if line.invoice_id.billing_ids:
                line.billing_date = line.invoice_id.billing_ids[0].date
                line.billing_due_date = line.invoice_id.billing_ids[0].billing_due_date
                line.spe_invoice = line.invoice_id.billing_ids[0].is_spe_invoice
                line.payment_period = line.invoice_id.billing_ids[0].payment_period.id
                line.billing_receipt_date = line.invoice_id.billing_ids[0].receipt_date
            else:
                line.billing_date = False
                line.billing_due_date = False
                line.spe_invoice = False
                line.payment_period = False
                line.billing_receipt_date = False
                
    @api.depends('messenger_job_id', 'messenger_job_id.state')
    def _compute_messenger_done_job(self):
        for line in self:
            if line.messenger_job_id and line.messenger_job_id.state == 'done':
                line.done_job = True
            else:
                line.done_job = False