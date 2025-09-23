# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class MessengerJobs(models.Model):
    _name = 'messenger.job'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Messenger Job'
    _rec_name = 'name'
    _order = 'id desc'

    name = fields.Char(string='Name', required=True, default='New', copy=False, tracking=True, readonly=True)
    responsible_person = fields.Many2one('res.users', string='Responsible', states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'confirm': [('readonly', True)]}, default=lambda self: self.env.user, required=True)
    messenger_name = fields.Many2one('hr.employee', string='Messenger Name', states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'confirm': [('readonly', True)]}, required=True)
    billing_route_id = fields.Many2one('account.billing.route', string='Billing Route', states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'confirm': [('readonly', True)]})
    payment_period_id = fields.Many2one('account.payment.period', string='Payment Period', states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'confirm': [('readonly', True)]})
    description = fields.Char(string='Description', states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'confirm': [('readonly', True)]})
    date = fields.Date(string='Date', default=fields.Date.context_today, states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'confirm': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('done', 'Done'),
        ('cancel', 'Cancel')
    ], string='Status', default='draft', tracking=True, states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'confirm': [('readonly', True)]})
    notes = fields.Text(string='Notes')
    responsible_person = fields.Many2one('res.users', string='Responsible', states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'confirm': [('readonly', True)]}, default=lambda self: self.env.user, required=True)
    line_ids = fields.One2many('messenger.job.line', 'messenger_job_id', string='Invoices', states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'confirm': [('readonly', True)]})
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    
    @api.model 
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('messenger.job') or 'New'
        return super(MessengerJobs, self).create(vals)
    
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_("You can only delete a Messenger Job in draft state."))
            record._unlink_messenger_job_id()
        return super(MessengerJobs, self).unlink()
    
    def action_confirm(self):
        self.ensure_one()
        # check line_ids if there is lines that already confirmed in other messenger job
        self._validate_lines()
        self.write({'state': 'confirm'})
        
    def action_done(self):
        self.ensure_one()
        self.write({ 'state': 'done'})
        invoices = self._get_invoices()
        if invoices:
            for inv in invoices:
                inv.write({
                    'messenger_job_id': self.id
                })
        
        self._update_batch_billing_line_state()    
        
        
    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancel'})
        self._unlink_messenger_job_id()
        
    def action_set_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        self._unlink_messenger_job_id()
        
    def action_multiple_selection_window(self):
        action = self.env['ir.actions.actions']._for_xml_id('bs_messenger_job.action_multiple_selection_wizard')
        return action
    
    
    def _validate_lines(self):
        batch_bill_lines = self.line_ids.mapped('batch_billing_line_id').ids
        confirmed_count = self.env['batch.billing.line'].search_count([('id', 'in', batch_bill_lines), ('done_job', '=', True)])
        confirmed_lines = self.env['batch.billing.line'].search([('id', 'in', batch_bill_lines), ('done_job', '=', True)])
        
        if confirmed_count > 0:
            confirmed_info = '\n'.join(
                f"- {p.display_name or p.id}, with Messenger Job: {p.messenger_job_id.name or p.messenger_job_id.id}"
                for p in confirmed_lines
            )
            raise ValidationError(_(
                "The following billing(s) have already been processed in another Messenger Job. \
                \nPlease remove these billing(s) from the current Messenger Job before proceeding.\n\n%s \
                "
            ) % confirmed_info)
    
    def _get_invoices(self):
        moves = self.line_ids.mapped('invoice_id')
        return moves
    
    def _unlink_messenger_job_id(self):
        invoices = self._get_invoices()
        if invoices:
            for inv in invoices:
                inv.write({
                    'messenger_job_id': False
                })
        # update batch billing line 
        self.line_ids.mapped('batch_billing_line_id').write({'messenger_job_id': False})
                
    def _update_batch_billing_line_state(self):
        for line in self.line_ids:
            line.batch_billing_line_id.write({'messenger_job_id': self.id})
    

class MessengerJobLine(models.Model):
    _name = 'messenger.job.line'
    _description = 'Messenger Job Line'
    
    messenger_job_id = fields.Many2one('messenger.job', string='Messenger Job', required=True, ondelete='cascade')
    batch_billing_line_id = fields.Many2one('batch.billing.line', string='Batch Billing Line', required=True, domain="[('batch_billing_id.state', '=', 'done'), ('done_job', '=', False)]")
    invoice_id = fields.Many2one('account.move', string='Invoice', related='batch_billing_line_id.invoice_id')
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, related='batch_billing_line_id.partner_id')
    billing_no = fields.Char(string='Billing No.', related='batch_billing_line_id.billing_no')
    spe_billing_no = fields.Char(string='SPE Billing No.', related='batch_billing_line_id.billing_no')
    billing_date = fields.Date(string='Billing Date', related='batch_billing_line_id.billing_date')
    invoice_no = fields.Char(string='Invoice No.', related='invoice_id.name')
    spe_invoice = fields.Char(string='SPE Invoice', related='invoice_id.form_no')
    invoice_date = fields.Date(string='Invoice Date', related='invoice_id.invoice_date')
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Term', related='invoice_id.invoice_payment_term_id')
    due_date = fields.Date(string='Due Date', related='invoice_id.invoice_date_due_payment_term')
    due_payment = fields.Date(string='Due Payment', related='invoice_id.due_payment')
    amount_due = fields.Monetary(string='Amount Due', currency_field='currency_id', related='batch_billing_line_id.amount_due')
    billing_route_id = fields.Many2one('account.billing.route', string='Billing Route', related='batch_billing_line_id.billing_route_id')
    name_1 = fields.Char(string='Name1')
    date_1 = fields.Date(string='Date1')
    remark_1 = fields.Char(string='Remark1')
    name_2 = fields.Char(string='Name2')
    date_2 = fields.Date(string='Date2')
    remark_2 = fields.Char(string='Remark2')
    name_3 = fields.Char(string='Name3')
    date_3 = fields.Date(string='Date3')
    remark_3 = fields.Char(string='Remark3')
    done_job = fields.Boolean(string='Done Job', default=False)
    
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id')
    
    
    def _filter_seletected_batch_billing_lines(self):
        self.ensure_one()
        lines = self.messenger_job_id.line_ids.filtered(lambda l: l.id != self.id)
        return lines.mapped('batch_billing_line_id').ids
    
    @api.onchange('batch_billing_line_id')    
    def _onchange_messenger_line_id(self):
        batch_billing_line_list = self._filter_seletected_batch_billing_lines()
        return {'domain': {'batch_billing_line_id': [('id', 'not in', batch_billing_line_list)]}}  