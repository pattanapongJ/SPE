# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class TempCreditRequest(models.Model):
    _name = 'temp.credit.request'
    _description = "Temp Credit Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    
    name = fields.Char(string = 'Temp Credit Request', readonly=True, index=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string = 'Customer', ondelete = 'cascade', required=True,
                                 index = True, copy = True, domain="[('customer', '=', True)]")
    customer_credit_limit = fields.Float(related="partner_id.credit_limit", string = 'Customer Credit Limit', digits = (16, 2))
    order_no = fields.Many2one('sale.order', string = 'Sale order No', required=True)

    credit_limit = fields.Float(string = "Credit Limit", digits = (16, 2), compute='_compute_credit_limit')
    credit_remain = fields.Float(string = "Credit Remain", digits = (16, 2), compute='_compute_credit_limit')
    sale_person = fields.Many2one('res.users', string = 'Sale Person', required=True)
    sale_team_id = fields.Many2one('crm.team', string = 'Sale Team', required = True, ondelete = 'cascade',
                                   index = True, copy = True)
    quotation_credit_limit = fields.Float(string = "Quotation Credit Limit",compute='_compute_credit_limit', readonly=True, digits = (16, 2))
    invoice_credit_limit = fields.Float(string = "Invoiced Credit Limit", compute='_compute_credit_limit', readonly=True, digits = (16, 2))
    temp_credit_value = fields.Float(string = "Temp Credit Approved", compute='_compute_temp_credit_value', readonly=True, digits = (16, 2))
    team_temp_credit_value = fields.Float(string = "Team Temp Credit Approved", compute='_compute_team_temp_credit_value', readonly = True, digits = (16, 2))

    order_line = fields.One2many(related="order_no.order_line")

    amount_untaxed = fields.Monetary(related="order_no.amount_untaxed")
    amount_tax = fields.Monetary(related="order_no.amount_tax")
    amount_total = fields.Monetary(related="order_no.amount_total")
    currency_id = fields.Many2one(related = 'order_no.currency_id', store = True)

    state = fields.Selection([
            ("draft", "Draft"),
            ("waiting_approval", "Waiting Approval"),
            ("approved", "Done"),
            ("cancel", "Cancelled")], "Status", default="draft", readonly=True,tracking=True,)
    
    approve_date = fields.Datetime('Approve Date',copy=False,tracking=True,)
    approve_user_id = fields.Many2one('res.users',string='Approved By',copy=False,tracking=True,)
    reason_approval = fields.Text("Reason Credit Approval",tracking=True,)
    temp_credit_history_line = fields.One2many('temp.credit.request.history', 'temp_credit_id', string = 'TCR History')
    so_invoice_amount = fields.Float(string="SO Invoice Amount", compute='_compute_so_invoice_amount',store=False)
    so_invoice_amount_store = fields.Float(string="SO Invoice Amount (Store)")
    remain_amount = fields.Float(string="Remain Amount", compute='_compute_remain_amount',store=True)
    
    def preview_invoices(self):
        self.ensure_one()
        team_ids = self.sale_team_id.id
        partner_ids = self.partner_id
        account_id = self.env['account.move'].search(
            [('team_id', '=', team_ids),
             ('partner_id', '=', partner_ids.id),
             ('move_type', '=', 'out_invoice'),
             ])

        domain = [('id', 'in', account_id.ids)]
        action = {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': domain
            }
        return action

    def _compute_team_temp_credit_value(self):
        for rec in self:
            team_temp_credit_value = 0
            temp_credit_id = self.env["temp.credit.request"].search([
                ("sale_team_id", "=", rec.sale_team_id.id),("state", "=", "approved")])
            for temp in temp_credit_id:
                team_temp_credit_value += temp.amount_total

            rec.team_temp_credit_value = team_temp_credit_value

    def _compute_temp_credit_value(self):
        for rec in self:
            temp_credit_value = 0
            temp_credit_id = self.env["temp.credit.request"].search(
                [("partner_id", "=", rec.partner_id.id), ("sale_team_id", "=", rec.sale_team_id.id),
                    ("state", "=", "approved")])

            for temp in temp_credit_id:
                temp_credit_value += temp.amount_total

            rec.temp_credit_value = temp_credit_value

    def _compute_credit_limit(self):
        for rec in self:
            credit_limit = 0
            credit_remain = 0
            quotation_credit_limit = 0
            invoice_credit_limit = 0
            customer_credit_id = self.env["customer.credit.limit"].search([("partner_id", "=", rec.partner_id.id)], limit=1)
            if customer_credit_id:
                credit_limit_sale = self.env["credit.limit.sale.line"].search([
                    ("credit_id", "=", customer_credit_id.credit_id.id),
                    ("sale_team_id", "=", rec.sale_team_id.id)])
                credit_limit = credit_limit_sale.credit_limit
                credit_remain = credit_limit_sale.credit_remain
                quotation_credit_limit = credit_limit_sale.quotation_amount
                invoice_credit_limit = credit_limit_sale.invoiced_amount

            rec.credit_limit = credit_limit
            rec.credit_remain = credit_remain
            rec.quotation_credit_limit = quotation_credit_limit
            rec.invoice_credit_limit = invoice_credit_limit
            # rec.temp_credit_value = temp_credit_value

    def action_confirm(self):
        for rec in self:
            rec.state = "waiting_approval"

    def action_approval(self):
        for rec in self:
            rec.state = "approved"
            rec.approve_date = datetime.now()
            rec.approve_user_id = rec.env.user.id

            approve_sequence = len(rec.temp_credit_history_line) + 1
            temp_credit_history_value = {
            'temp_credit_id': rec.id, 
            'approve_sequence': approve_sequence,
            'approve_date': datetime.now(),
            'approve_amount': rec.remain_amount, 
            }
            rec.order_no.approve_credit_amount = rec.remain_amount
            temp_credit_history_id = rec.env['temp.credit.request.history'].create(temp_credit_history_value)

    def action_cancel(self):
        for rec in self:
            rec.order_no.state = "draft"
            rec.state = "cancel"


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('sequence_credit_request') or _('New')
        result = super(TempCreditRequest, self).create(vals)
        return result
    
    def check_iso_name(self, check_iso):
        for purchase in self:
            check_model = self.env["ir.actions.report"].search([('model', '=', 'temp.credit.request'),('report_name', '=', check_iso)], limit=1)
            if check_model:
                return check_model.iso_name
            else:
                return "-"
            
    def print_credit_limit_request_report(self):
        self.ensure_one()
        return {
            "name": "Report",
            "type": "ir.actions.act_window",
            "res_model": "wizard.temp.credit.request.report",
            "view_mode": 'form',
            'target': 'new',
            "context": {
                "default_temp_credit_id": self.id,
                },
        }
    
    def check_other_request(self):
        check_request = self.env["temp.credit.request"].search([('partner_id', '=', self.partner_id.id),('id','!=',self.id),('state','=','waiting_approval')])
        request_list = []
        count = 0
        so_name1 = ""
        so_name2 = ""
        total1 = 0
        total2 = 0
        for request in check_request:
            count += 1
            if count %2 == 1:
                so_name1 = request.order_no.name
                total1 = request.remain_amount
            if count %2 == 0:
                so_name2 = request.order_no.name
                total2 = request.remain_amount
                request_list.append([2,so_name1,total1,so_name2,total2,])
        if count %2 == 1:
            request_list.append([1,so_name1,total1])
        request_box = []
        request_box = [request_list[i:i+5] for i in range(0, len(request_list), 5)]
        return request_box
    
    def get_project_name_list(self):
        check_request = self.env["temp.credit.request"].search([('partner_id', '=', self.partner_id.id),('id','!=',self.id),('state','=','waiting_approval')])
        project_name_list = ""
        for request in check_request:
            if request.order_no.project_name:
                if len(project_name_list) == 0:
                    project_name_list = request.order_no.project_name.project_name
                else:
                    project_name_list = project_name_list + "," + request.order_no.project_name.project_name
        return project_name_list
    
    def get_reason_approval_list(self):
        check_request = self.env["temp.credit.request"].search([('partner_id', '=', self.partner_id.id),('id','!=',self.id),('state','=','waiting_approval')])
        reason_approval_list = ""
        if self.reason_approval:
            reason_approval_list = self.reason_approval
        for request in check_request:
            if request.reason_approval:
                if len(reason_approval_list) == 0:
                    reason_approval_list = request.reason_approval
                else:
                    reason_approval_list = reason_approval_list + "," + request.reason_approval
        return reason_approval_list
    
    @api.depends('order_no.invoice_ids', 'order_no.invoice_ids.state', 'order_no.invoice_ids.amount_total')
    def _compute_so_invoice_amount(self):
        for rec in self:
            invoice_amount_total_sum = 0 
            for invoice in rec.order_no.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice' and inv.state != 'cancel'):
                invoice_amount_total_sum += invoice.amount_total
            rec.so_invoice_amount = invoice_amount_total_sum
            rec.so_invoice_amount_store = invoice_amount_total_sum

    @api.depends('amount_total', 'so_invoice_amount_store')
    def _compute_remain_amount(self):
        for rec in self:
            rec.remain_amount = rec.amount_total - rec.so_invoice_amount

    def check_approval_expiry(self,days=7):
        if days <= 0:
            return
        
        domain = [('state', '=', 'approved'),('remain_amount', '>', 0)]
        temp_credit_ids = self.env['temp.credit.request'].search(domain)
        today_date = fields.Date.context_today(self)

        for temp in temp_credit_ids:
            latest_line = temp.temp_credit_history_line.sorted(
                key=lambda l: l.approve_sequence, reverse=True
            )[:1]
            if not latest_line:
                continue

            approve_date = latest_line.approve_date.date() if latest_line.approve_date else None
            if not approve_date:
                continue
            else:
                delta_days = (today_date - approve_date).days
                if delta_days >= days:
                    temp.state = 'waiting_approval'
                    temp.order_no.state = 'credit_limit'
    
    def name_get(self):
        result = []
        for rec in self:
            name = rec.name + ' [' + rec.order_no.name + ']'
            result.append((rec.id, name))
        return result
    
class TempCreditRequestHistory(models.Model):
    _name = 'temp.credit.request.history'
    _description = "Temp Credit Request History"

    temp_credit_id = fields.Many2one('temp.credit.request', string = 'Temp Credit Request')
    approve_sequence = fields.Integer(string="No",readonly=True,copy=False,)
    approve_date = fields.Datetime('Date Approved',copy=False,)
    approve_amount = fields.Float('Approve Amount', required=True, digits='Product Price', default=0.0)
    note = fields.Text("Note")