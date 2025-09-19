# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError


class CreditLimitSale(models.Model):
    _name = 'credit.limit.sale'
    _description = "Credit Limit Sales"
    _inherit = ["mail.thread"]

    name = fields.Char(string="Credit Limit Name",tracking=True, required=True)
    total_credit = fields.Float(string="Total Credit Limit", digits=(16, 2),tracking=True, compute='_compute_total_credit')
    credit_limit_remain_total = fields.Float(string="Total remaining credit limit", digits=(16, 2), compute='_compute_credit_limit_remain')
    cash_limit_remain_total = fields.Float(string="Total remaining Cash limit", digits=(16, 2), compute='_compute_credit_limit_remain')
    cash_limit = fields.Float(string="Cash Limit", digits=(16, 2),tracking=True,)
    credit_limit_hold = fields.Boolean(string="Credit Limit Hold", store=True,tracking=True,)
    credit_line = fields.One2many('credit.limit.sale.line', 'credit_id',
                                 string='Credit Limit by Sales', copy=False, auto_join=True,)
    note = fields.Text("Remark",tracking=True,)
    group_type = fields.Selection(
        selection=[
            ("type_group", "Group"),
            ("type_individual", "Table"),
        ],
        string="Type",
        required=True,
        default="type_group",
    ) 
    credit_line_person = fields.One2many('credit.limit.sale.person.line', 'credit_id',
                                 string='Credit Limit by Sales Person', copy=False, auto_join=True,)
    remark_on_hold = fields.Text("Remark On Hold",tracking=True)
    
    def _compute_credit_limit_remain(self):
        for rec in self:
            customer_credit_ids = self.env['customer.credit.limit'].search([('credit_id', '=', rec.id)])
            sum_credit_remain = 0
            for line in rec.credit_line:
                sum_credit_remain += line.credit_remain
            rec.credit_limit_remain_total = sum_credit_remain
            sale_order_amount_cash = 0
            invoiced_amount_draft_cash = 0
            invoice_cash_amount = 0
            sale_order_amount_cash = sum([line.sale_order_amount_cash for line in customer_credit_ids])
            invoiced_amount_draft_cash = sum([line.invoiced_amount_draft_cash for line in customer_credit_ids])
            invoice_cash_amount = sum([line.invoice_cash_amount for line in customer_credit_ids])
            rec.cash_limit_remain_total = rec.cash_limit - (sale_order_amount_cash + invoiced_amount_draft_cash + invoice_cash_amount)

    def _compute_total_credit(self):
        for rec in self:
            total = 0.0
            for line in rec.credit_line:
                total += line.credit_limit
            rec.total_credit = total

    @api.onchange("total_credit", "credit_limit_hold","credit_limit_remain_total")
    def _onchange_total_credit(self):
        for rec in self:
            customer_credit_id = self.env["customer.credit.limit"].search([("credit_id", "=", rec._origin.id)])
            for cus in customer_credit_id:
                cus.partner_id.check_credit = True
                cus.partner_id.credit_limit_on_hold = rec.credit_limit_hold
                # cus.partner_id.credit_limit = rec.total_credit
                cus.partner_id.credit_limit = rec.credit_limit_remain_total

    def preview_credit_limit_by_sale_team(self):
        self.ensure_one()
        sale_list = []
        order_id = self.env['sale.order']
        for rec in self.credit_line:
            customer_credit_id = rec.env["customer.credit.limit"].search([("credit_id", "=", rec.credit_id.id)])
            all_partner_ids = customer_credit_id.mapped('partner_id').ids
            partner_ids = customer_credit_id.mapped('partner_id')
            for partner in partner_ids:
                if partner.parent_id:
                    all_partner_ids.append(partner.parent_id.id)
                else:
                    all_partner_ids.append(partner.id)
            order_id |= self.env['sale.order'].search([('team_id', '=', rec.sale_team_id.id),
                                                      ('partner_id', 'in', all_partner_ids),
                                                      ('type_id.is_credit_limit', '=', True),
                                                      ('state', 'in', ('sale', 'done')),
                                                      ('payment_term_id', '=', rec.payment_term_id.id),
                                                      ('payment_term_id.is_cash', '=', False),])
   
        for order in order_id:
            sale_list.append(order.id)
        domain = [('id', 'in', sale_list)]
        action = {
            'name': _('Credit Limit by Sales Team'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree',
            "views": [(self.env.ref("hdc_creditlimit_saleteam.view_quotation_tree_on_credit").id, "tree")],
            'domain': domain,
            'context': {'default_credit_id': self.id},
            }
        return action
    

    def preview_sale_order(self):
        self.ensure_one()
        sale_list = []
        team_ids = self.credit_line.mapped('sale_team_id').ids
        customer_credit_id = self.env["customer.credit.limit"].search([("credit_id", "=", self.id)])
        partner_ids = customer_credit_id.mapped('partner_id').ids
        temp_ids = self.env['temp.credit.request'].search(
            [('sale_team_id', 'in', team_ids), ('partner_id', 'in', partner_ids),('state','in',['draft','waiting_approval'])])
        for temp_id in temp_ids:
            sale_list.append(temp_id.order_no.id)
        domain = [('id', '=', sale_list)]
        action = {
            'name': _('Sale Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'default_credit_id': self.id},
            }
        return action
    
    def preview_customer(self):
        self.ensure_one()
        domain = [('credit_id', '=', self.id)]
        action = {
            'name': _('Customers'),
            'type': 'ir.actions.act_window',
            'res_model': 'customer.credit.limit',
            "views": [(self.env.ref("hdc_creditlimit_saleteam.view_customer_credit_limit_tree").id, "tree"),(self.env.ref("hdc_creditlimit_saleteam.view_customer_credit_limit_form").id, "form")],
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'default_credit_id': self.id},
            }
        return action

    def preview_credit_limit(self):
        team_ids = self.credit_line.mapped('sale_team_id').ids
        customer_credit_id = self.env["customer.credit.limit"].search([("credit_id", "=", self.id)])
        partner_ids = customer_credit_id.mapped('partner_id').ids
        temp_id = self.env['temp.credit.request'].search(
            [('sale_team_id', 'in', team_ids), ('partner_id', 'in', partner_ids)])
        action = {
            'name': "Temp Credit Request",
            'view_mode': 'tree,form',
            'view_id': False,
            'res_model': 'temp.credit.request',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', temp_id.ids)],
            }
        return action
    
    def preview_customer_cash(self):
        self.ensure_one()
        domain = [('credit_id', '=', self.id)]
        action = {
            'name': _('Customers Cash Limit'),
            'type': 'ir.actions.act_window',
            'res_model': 'customer.credit.limit',
            "views": [(self.env.ref("hdc_creditlimit_saleteam.view_customer_cash_limit_tree").id, "tree"),
                      (self.env.ref("hdc_creditlimit_saleteam.view_customer_cash_limit_form").id, "form")],
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'default_credit_id': self.id},
            }
        return action

    def preview_invoices(self):
        self.ensure_one()
        team_ids = self.credit_line.mapped('sale_team_id').ids
        customer_credit_id = self.env["customer.credit.limit"].search([("credit_id", "=", self.id)])
        partner_ids = customer_credit_id.mapped('partner_id').ids
        account_id = self.env['account.move'].search(
            [('team_id', 'in', team_ids), ('partner_id', 'in', partner_ids),
             ('move_type', '=', 'out_invoice'),('payment_state', 'not in', ('paid', 'partial'))])

        domain = [('id', 'in', account_id.ids)]
        action = {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': domain
            }
        return action

    def preview_credit_approved(self):
        self.ensure_one()
        team_ids = self.credit_line.mapped('sale_team_id').ids
        customer_credit_id = self.env["customer.credit.limit"].search([("credit_id", "=", self.id)])
        partner_ids = customer_credit_id.mapped('partner_id').ids
        account_id = self.env['account.move'].search(
            [('team_id', 'in', team_ids), ('partner_id', 'in', partner_ids),
             ('move_type', '=', 'out_invoice'),('payment_state', 'in', ('paid', 'partial'))])

        domain = [('id', 'in', account_id.ids)]
        action = {
            'name': _('Credit Approved'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': domain
            }
        return action

class CreditLimitSaleLine(models.Model):
    _name = 'credit.limit.sale.line'
    _description = "Credit Limit by Sales"
    _inherit = ['mail.thread']

    credit_id = fields.Many2one('credit.limit.sale', string = 'Credit Limit Sales', required = True,
                                ondelete = 'cascade', index = True, copy = False,tracking=True,)
    sale_team_id = fields.Many2one('crm.team', string = 'Sale Team', required = True,
                                ondelete = 'cascade', index = True, copy = False,tracking=True,)
    credit_limit = fields.Float(string = "Credit Limit", digits=(16, 2),tracking=True,)
    quotation_amount = fields.Float(string = "Quotation Amount", digits=(16, 2), compute='_compute_quotation_amount')
    sale_order_amount = fields.Float(string = "Sale Order Amount", digits=(16, 2), compute='_compute_sale_amount')
    invoiced_amount_draft = fields.Float(string = "Invoiced (Draft) Amount", digits=(16, 2), compute='_compute_invoiced_amount_draft')
    invoiced_amount = fields.Float(string = "Invoiced Amount", digits=(16, 2), compute='_compute_invoiced_amount')
    credit_remain = fields.Float(string = "Credit Remain", digits=(16, 2), compute='_compute_credit_remain')
    credit_approval = fields.Float(string = "Credit Approval", digits=(16, 2), compute='_compute_credit_approval')
    payment_term_id = fields.Many2one(comodel_name = "account.payment.term", string = "Payment Terms",tracking=True,)
    payment_method_id = fields.Many2one('account.payment.method', string ='Payment Method',tracking=True,)
    note = fields.Text(string ='Remark',tracking=True,)
    name = fields.Char(string='Name', compute='_compute_name', store=True, readonly=False)
    sale_user_id = fields.Many2one('res.users', string = 'Sale Person', tracking = True, domain="[('id', 'in', member_ids)]")
    
    @api.depends('sale_team_id')
    def _compute_member_ids(self):
        for rec in self:
            rec.member_ids = rec.sale_team_id.member_ids.ids
    member_ids = fields.Many2many('res.users', compute = "_compute_member_ids")

    @api.depends('sale_team_id')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.sale_team_id.name if rec.sale_team_id else rec.id

    def _compute_invoiced_amount_draft(self):
        for rec in self:
            customer_credit_id = self.env["customer.credit.limit"].search([("credit_id", "=", rec.credit_id.id)])
            partner_ids = customer_credit_id.mapped('partner_id').ids
            account_id = self.env['account.move'].search([('team_id', '=', rec.sale_team_id.id),
                                                      ('partner_id', 'in', partner_ids),('is_cash', '=', False),
                                                      ('state', '=', 'draft'), ('move_type', '=', 'out_invoice')])

            invoiced_amount = 0
            for acc in account_id:
                invoiced_amount += acc.amount_total

            rec.invoiced_amount_draft = invoiced_amount

    def _compute_invoiced_amount(self):
        for rec in self:
            customer_credit_id = self.env["customer.credit.limit"].search([("credit_id", "=", rec.credit_id.id)])
            partner_ids = customer_credit_id.mapped('partner_id').ids
            account_id = self.env['account.move'].search([('team_id', '=', rec.sale_team_id.id),
                                                      ('partner_id', 'in', partner_ids),('is_cash', '=', False),
                                                      ('state', '=', 'posted'), ('move_type', '=', 'out_invoice')])

            invoiced_amount = 0
            payment_amount = 0
            for acc in account_id:
                # invoiced_amount += acc.amount_total
                invoiced_amount += acc.amount_residual
            account_entry_id = self.env['account.move'].search(
                [('team_id', '=', rec.sale_team_id.id),('partner_id', 'in', partner_ids), ('state', '=', 'posted'), ('move_type', '=', 'entry')])

            account_payment = self.env['account.payment'].search(
                [('move_id', 'in', account_entry_id.ids),('is_cheque', '=', True)])
            account_payment_done = self.env['account.payment'].search(
                [('move_id', 'in', account_entry_id.ids),('pdc_id.state', '=', 'done'),('is_cheque', '=', True)])
            for payment in account_payment:
                payment_amount += payment.amount
            for payment_done in account_payment_done:
                payment_amount -= payment_done.pdc_id.payment_amount

            rec.invoiced_amount = invoiced_amount + payment_amount

    # @api.onchange("credit_limit")
    # def _onchange_credit_limit(self):
    #     default_credit_id = self.credit_id._origin.id
    #     if self.credit_id:
    #         credit_id = self.env['credit.limit.sale'].browse(default_credit_id)
    #         credit_limit_sale = self.env["credit.limit.sale.line"].search([("credit_id", "=", default_credit_id)])
    #         credit_limit = self.credit_limit
    #         for rec in credit_limit_sale:
    #             credit_limit += rec.credit_limit
    #
    #         # if credit_limit > credit_id.total_credit:
    #         #     raise UserError(_("Credit Limit Over Total Credit Limit"))
    #         credit_id.total_credit = credit_limit

    @api.onchange("sale_team_id")
    def _onchange_sale_team(self):
        default_credit_id = self.credit_id._origin.id
        if default_credit_id:
            credit_id = self.env["credit.limit.sale.line"].search([("credit_id", "=", default_credit_id)])
            if credit_id:
                sale_team_id = credit_id.mapped('sale_team_id').ids
                return {"domain": {"sale_team_id": [('id', 'not in', sale_team_id)]}}
        return []

    def _compute_quotation_amount(self):
        for rec in self:
            customer_credit_id = rec.env["customer.credit.limit"].search([("credit_id", "=", rec.credit_id.id)])
            all_partner_ids = customer_credit_id.mapped('partner_id').ids
            partner_ids = customer_credit_id.mapped('partner_id')
            for partner in partner_ids:
                if partner.parent_id:
                    all_partner_ids.append(partner.parent_id.id)
                else:
                    all_partner_ids.append(partner.id)
            order_id = self.env['sale.order'].search([('team_id', '=', rec.sale_team_id.id),
                                                      ('partner_id', 'in', all_partner_ids),
                                                      ('type_id.is_credit_limit', '=', True),
                                                      ('state', 'in', ('draft', 'sent',))])
            quotation_amount = 0
            for sale in order_id:
                if sale.payment_term_id and sale.payment_term_id.is_cash == False:
                    quotation_amount += sale.amount_total
            rec.quotation_amount = quotation_amount

    def _compute_sale_amount(self):
        for rec in self:
            customer_credit_id = rec.env["customer.credit.limit"].search([("credit_id", "=", rec.credit_id.id)])
            all_partner_ids = customer_credit_id.mapped('partner_id').ids
            partner_ids = customer_credit_id.mapped('partner_id')
            for partner in partner_ids:
                if partner.parent_id:
                    all_partner_ids.append(partner.parent_id.id)
                else:
                    all_partner_ids.append(partner.id)
            order_id = self.env['sale.order'].search([('team_id', '=', rec.sale_team_id.id),
                                                      ('partner_id', 'in', all_partner_ids),
                                                      ('type_id.is_credit_limit', '=', True),
                                                      ('state', 'in', ('sale', 'done'))])
            sale_order_amount = 0
            for sale in order_id:
                if sale.payment_term_id and sale.payment_term_id.is_cash == False:
                    if sale.invoice_count == 0:
                        sale_order_amount += sale.amount_total
                    else:
                        total_invoice = 0
                        for inv in sale.invoice_ids:
                            if inv.state != 'cancel':
                                total_invoice += inv.amount_total
                        sale_order_amount += (sale.amount_total - total_invoice)

            rec.sale_order_amount = sale_order_amount

    def _compute_credit_approval(self):
        for rec in self:
            rec.credit_approval = rec.credit_limit - rec.credit_remain

    def _compute_credit_remain(self):
        for rec in self:
            rec.credit_remain = rec.credit_limit - (rec.sale_order_amount + rec.invoiced_amount_draft + rec.invoiced_amount)
            # rec.credit_remain = rec.credit_limit

    def write(self, vals):
        tracked_fields = self._get_tracked_fields()
        changes = []
        ARROW_RIGHT = '<div class="o_Message_trackingValueSeparator o_Message_trackingValueItem fa fa-long-arrow-right" title="Changed" role="img"></div>'
        
        for field in tracked_fields:
            if field in vals:
                old_value = self[field].display_name if self._fields[field].type == 'many2one' else self[field]
                new_value = self.env[self._fields[field].comodel_name].browse(vals.get(field)).display_name if self._fields[field].type == 'many2one' else vals.get(field)
                if old_value != new_value:
                    changes.append(f"<li>{self.fields_get([field])[field]['string']}: {old_value} {ARROW_RIGHT} {new_value}</li>")
        if changes:
            message = f"<p>Credit Limit by Sales: {self.sale_team_id.display_name}</p><ul>" + "".join(changes) + "</ul>"
            self.message_post(body=message)
            if self.credit_id:
                self.credit_id.message_post(body=message)
        return super(CreditLimitSaleLine, self).write(vals)



class CustomerCreditLimit(models.Model):
    _name = 'customer.credit.limit'
    _description = "Customer Credit"

    @api.model
    def _domain_customer(self):
        credit_id = self.env["customer.credit.limit"].search([])
        if credit_id:
            partner_id = credit_id.mapped('partner_id').ids
            return [('customer', '=', True), ('id', 'not in', partner_id)]
        return [('customer', '=', True)]


    credit_id = fields.Many2one('credit.limit.sale', string = 'Credit Limit Sales', required = True,
                                ondelete = 'cascade', index = True, copy = False)
    partner_id = fields.Many2one('res.partner', string = 'Customer', required = True,
                                ondelete = 'cascade', index = True, copy = False, domain=lambda self: self._domain_customer())
    partner_ref = fields.Char(related='partner_id.ref',string="Partner ID",store=True)
    contact_address = fields.Char(related='partner_id.contact_address', string='Complete Address')

    credit_limit = fields.Float(related="partner_id.credit_limit", string = "Credit Limit", digits = (16, 2))
    cash_limit = fields.Float(related="partner_id.cash_limit", string = "Cash Limit", digits = (16, 2))
    sale_order_amount = fields.Float(string = "Sale Order Amount", digits = (16, 2), compute = '_compute_sale_amount')
    sale_order_amount_cash = fields.Float(string = "Sale Order Amount (Cash)", digits = (16, 2), compute = '_compute_sale_amount_cash')
    credit_limit_show = fields.Float(related="partner_id.credit_limit_show", string ="Credit Limit")
    cash_limit_show = fields.Float(related="partner_id.cash_limit_show", string ="Cash Limit")
    quotation_amount = fields.Float(compute="_compute_quotation_amount", string = "Quotation Amount", digits = (16, 2))
    quotation_amount_cash = fields.Float(compute="_compute_quotation_amount_cash", string = "Quotation Amount (Cash)", digits = (16, 2))
    invoiced_amount_draft = fields.Float(string = "Invoiced (Draft) Amount", digits=(16, 2), compute='_compute_invoiced_amount_draft')
    invoiced_amount_draft_cash = fields.Float(string = "Invoiced (Draft) Amount (Cash) ", digits=(16, 2), compute='_compute_invoiced_amount_draft_cash')
    invoice_amount = fields.Float(string = "Invoice Amount", digits = (16, 2), compute="_compute_invoiced_amount")
    invoice_cash_amount = fields.Float(string = "Invoice Amount (Cash)", digits = (16, 2), compute="_compute_invoiced_amount")
    credit_remain = fields.Float(string = "Credit Remain", digits = (16, 2), compute="_compute_credit_remain")
    cash_remain = fields.Float(string = "Cash Remain", digits = (16, 2), compute="_compute_credit_remain")
    credit_approval = fields.Float(string = "Credit Approval", digits = (16, 2), compute="_compute_credit_approval")
    cash_approval = fields.Float(string = "Cash Approval", digits = (16, 2), compute="_compute_credit_approval")

    def _compute_invoiced_amount_draft(self):
        for rec in self:
            sale_team_ids = rec.credit_id.credit_line.mapped('sale_team_id.id')
            account_id = self.env['account.move'].search([('partner_id', '=', rec.partner_id.id),
                                                      ('state', '=', 'draft'), ('move_type', '=', 'out_invoice'),('is_cash', '=', False),('team_id', 'in', sale_team_ids)])
            invoiced_amount = 0
            for acc in account_id:
                invoiced_amount += acc.amount_total

            rec.invoiced_amount_draft = invoiced_amount

    def _compute_invoiced_amount_draft_cash(self):
        for rec in self:
            account_id = self.env['account.move'].search([('partner_id', '=', rec.partner_id.id),
                                                      ('state', '=', 'draft'), ('move_type', '=', 'out_invoice'),('is_cash', '=', True)])
            invoiced_amount = 0
            for acc in account_id:
                invoiced_amount += acc.amount_total

            rec.invoiced_amount_draft_cash = invoiced_amount

    def _compute_invoiced_amount(self):
        for rec in self:
            sale_team_ids = rec.credit_id.credit_line.mapped('sale_team_id.id')
            account_id = self.env['account.move'].search([('partner_id', '=', rec.partner_id.id),
                                                      ('state', '=', 'posted'), ('move_type', '=', 'out_invoice'),('team_id', 'in', sale_team_ids)])

            invoiced_amount_credit = 0
            invoiced_amount_cash = 0
            payment_amount = 0
            for acc in account_id.filtered(lambda l: l.is_cash == False):
                invoiced_amount_credit += acc.amount_residual
            for acc in account_id.filtered(lambda l: l.is_cash == True):
                invoiced_amount_cash += acc.amount_residual
            account_entry_id = self.env['account.move'].search(
                [('partner_id', '=', rec.partner_id.id), ('state', '=', 'posted'), ('move_type', '=', 'entry')])

            account_payment = self.env['account.payment'].search(
                [('move_id', 'in', account_entry_id.ids),('is_cheque', '=', True)])
            account_payment_done = self.env['account.payment'].search(
                [('move_id', 'in', account_entry_id.ids),('pdc_id.state', '=', 'done'),('is_cheque', '=', True)])
            for payment in account_payment:
                payment_amount += payment.amount
            for payment_done in account_payment_done:
                payment_amount -= payment_done.pdc_id.payment_amount
            rec.invoice_amount = invoiced_amount_credit + payment_amount
            rec.invoice_cash_amount = invoiced_amount_cash

    @api.model
    def create(self, vals):
        res = super(CustomerCreditLimit, self).create(vals)
        res.partner_id.credit_type = 'credit'
        res.partner_id.check_credit = True
        # res.partner_id.credit_limit_on_hold = True
        res.partner_id.credit_limit = res.credit_id.total_credit
        res.partner_id.cash_limit = res.credit_id.cash_limit
        return res
    
    def unlink(self):
        if not self.env.context.get('skip_partner_write', False):
            for rec in self:
                rec.partner_id.with_context(skip_credit_limit_unlink=True).write({
                    # 'check_credit': False,
                    'credit_limit_on_hold': False,
                    'credit_type': 'new'
                })
        return super(CustomerCreditLimit, self).unlink()

    def _compute_quotation_amount(self):
        for rec in self:
            sale_team_ids = rec.credit_id.credit_line.mapped('sale_team_id.id')
            order_id = self.env['sale.order'].search([('partner_id', '=', rec.partner_id.id),
                                                      ('type_id.is_credit_limit', '=', True),
                                                      ('state', 'in', ('draft', 'sent')),
                                                      ('team_id', 'in', sale_team_ids)])
            quotation_amount = 0
            for sale in order_id:
                if sale.payment_term_id and sale.payment_term_id.is_cash == False:
                    quotation_amount += sale.amount_total
            rec.quotation_amount = quotation_amount

    def _compute_quotation_amount_cash(self):
        for rec in self:
            order_id = self.env['sale.order'].search([('partner_id', '=', rec.partner_id.id),
                                                      ('type_id.is_credit_limit', '=', True),
                                                      ('state', 'in', ('draft', 'sent'))])
            quotation_amount = 0
            for sale in order_id:
                if sale.payment_term_id and sale.payment_term_id.is_cash == True:
                    quotation_amount += sale.amount_total
            rec.quotation_amount_cash = quotation_amount

    def _compute_sale_amount(self):
        for rec in self:
            sale_team_ids = rec.credit_id.credit_line.mapped('sale_team_id.id')
            order_id = self.env['sale.order'].search([('partner_id', '=', rec.partner_id.id),
                                                      ('type_id.is_credit_limit', '=', True),
                                                      ('state', 'in', ('sale', 'done')),
                                                      ('team_id', 'in', sale_team_ids)])
            sale_order_amount = 0
            for sale in order_id:
                if sale.payment_term_id and sale.payment_term_id.is_cash == False:
                    if sale.invoice_count == 0:
                        sale_order_amount += sale.amount_total
                    else:
                        total_invoice = 0
                        for inv in sale.invoice_ids:
                            if inv.state != 'cancel':
                                total_invoice += inv.amount_total
                        sale_order_amount += (sale.amount_total - total_invoice)

            rec.sale_order_amount = sale_order_amount

    def _compute_sale_amount_cash(self):
        for rec in self:
            order_id = self.env['sale.order'].search([('partner_id', '=', rec.partner_id.id),
                                                      ('type_id.is_credit_limit', '=', True),
                                                      ('state', 'in', ('sale', 'done'))])
            sale_order_amount = 0
            for sale in order_id:
                if sale.payment_term_id and sale.payment_term_id.is_cash == True:
                    if sale.invoice_count == 0:
                        sale_order_amount += sale.amount_total
                    else:
                        total_invoice = 0
                        for inv in sale.invoice_ids:
                            if inv.state != 'cancel':
                                total_invoice += inv.amount_total
                        sale_order_amount += (sale.amount_total - total_invoice)

            rec.sale_order_amount_cash = sale_order_amount

    def _compute_credit_approval(self):
        for rec in self:
            rec.credit_approval = rec.credit_limit_show - rec.credit_remain
            rec.cash_approval = rec.cash_limit_show - rec.cash_remain

    def _compute_credit_remain(self):
        for rec in self:
            # rec.credit_remain = rec.credit_limit - rec.invoice_amount
            rec.credit_remain = rec.credit_limit
            rec.cash_remain = rec.cash_limit

    @api.onchange("partner_id")
    def _onchange_customer(self):
        credit_id = self.env["customer.credit.limit"].search([('partner_id', '!=', self._origin.partner_id.id)])
        if credit_id:
            partner_id = credit_id.mapped('partner_id').ids
            partner_id.append(self.partner_id.id)
            return {"domain": {"partner_id": [('id', 'not in', partner_id), ('customer', '=', True)]}}
        return {"domain": {"partner_id": [('customer', '=', True)]}}
    
class CustomerCashLimit(models.Model):
    _name = 'customer.cash.limit'
    _description = "Customer Cash"

    @api.model
    def _domain_customer(self):
        credit_id = self.env["customer.cash.limit"].search([])
        if credit_id:
            partner_id = credit_id.mapped('partner_id').ids
            return [('customer', '=', True), ('id', 'not in', partner_id)]
        return [('customer', '=', True)]


    partner_id = fields.Many2one('res.partner', string = 'Customer', required = True,
                                ondelete = 'cascade', index = True, copy = False, domain=lambda self: self._domain_customer())
    partner_ref = fields.Char(related='partner_id.ref',string="Partner ID",store=True)
    contact_address = fields.Char(related='partner_id.contact_address', string='Complete Address')

    company_id = fields.Many2one(related='partner_id.company_id', string='Company', index=True,store=True)
    cash_limit_default = fields.Float(string ="Cash Limit Default",default=40000)
    cash_limit = fields.Float(string = "Cash Limit", digits = (16, 2),default=40000)
    quotation_amount_cash = fields.Float(compute="_compute_quotation_amount_cash", string = "Quotation Amount (Cash)", digits = (16, 2))
    sale_order_amount_cash = fields.Float(string = "Sale Order Amount (Cash)", digits = (16, 2), compute = '_compute_sale_amount_cash')
    invoiced_amount_draft_cash = fields.Float(string = "Invoiced (Draft) Amount (Cash) ", digits=(16, 2), compute='_compute_invoiced_amount_draft_cash')
    invoice_cash_amount = fields.Float(string = "Invoice Amount (Cash)", digits = (16, 2), compute="_compute_invoiced_amount")
    cash_remain = fields.Float(string = "Cash Remain", digits = (16, 2), compute="_compute_cash_remain")
    cash_approval = fields.Float(string = "Cash Approval", digits = (16, 2), compute="_compute_cash_approval")

    def _compute_invoiced_amount_draft_cash(self):
        for rec in self:
            account_id = self.env['account.move'].search([('partner_id', '=', rec.partner_id.id),
                                                      ('state', '=', 'draft'), ('move_type', '=', 'out_invoice'),('is_cash', '=', True)])
            invoiced_amount = 0
            for acc in account_id:
                invoiced_amount += acc.amount_total

            rec.invoiced_amount_draft_cash = invoiced_amount

    def _compute_invoiced_amount(self):
        for rec in self:
            account_id = self.env['account.move'].search([('partner_id', '=', rec.partner_id.id),
                                                      ('state', '=', 'posted'), ('move_type', '=', 'out_invoice'),('is_cash', '=', True)])

            invoiced_amount_cash = 0
            for acc in account_id:
                invoiced_amount_cash += acc.amount_residual
            rec.invoice_cash_amount = invoiced_amount_cash

    def _compute_quotation_amount_cash(self):
        for rec in self:
            order_id = self.env['sale.order'].search([('partner_id', '=', rec.partner_id.id),
                                                      ('type_id.is_credit_limit', '=', True),
                                                      ('state', 'in', ('draft', 'sent'))])
            quotation_amount = 0
            for sale in order_id:
                if sale.payment_term_id and sale.payment_term_id.is_cash == True:
                    quotation_amount += sale.amount_total
            rec.quotation_amount_cash = quotation_amount

    def _compute_sale_amount_cash(self):
        for rec in self:
            order_id = self.env['sale.order'].search([('partner_id', '=', rec.partner_id.id),
                                                      ('type_id.is_credit_limit', '=', True),
                                                      ('state', 'in', ('sale', 'done'))])
            sale_order_amount = 0
            for sale in order_id:
                if sale.payment_term_id and sale.payment_term_id.is_cash == True:
                    if sale.invoice_count == 0:
                        sale_order_amount += sale.amount_total
                    else:
                        total_invoice = 0
                        for inv in sale.invoice_ids:
                            if inv.state != 'cancel':
                                total_invoice += inv.amount_total
                        sale_order_amount += (sale.amount_total - total_invoice)

            rec.sale_order_amount_cash = sale_order_amount

    def _compute_cash_approval(self):
        for rec in self:
            rec.cash_approval = rec.cash_limit - rec.cash_remain

    def _compute_cash_remain(self):
        for rec in self:
            rec.cash_remain = rec.cash_limit - (rec.sale_order_amount_cash + rec.invoiced_amount_draft_cash + rec.invoice_cash_amount)

    @api.onchange("partner_id")
    def _onchange_customer(self):
        credit_id = self.env["customer.credit.limit"].search([('partner_id', '!=', self._origin.partner_id.id)])
        if credit_id:
            partner_id = credit_id.mapped('partner_id').ids
            partner_id.append(self.partner_id.id)
            return {"domain": {"partner_id": [('id', 'not in', partner_id), ('customer', '=', True)]}}
        return {"domain": {"partner_id": [('customer', '=', True)]}}
    
class CreditLimitSalePersonLine(models.Model):
    _name = 'credit.limit.sale.person.line'
    _description = "Credit Limit by Sales Person"
    _inherit = ['mail.thread']

    credit_id = fields.Many2one('credit.limit.sale', string = 'Credit Limit Sales', required = True,
                                ondelete = 'cascade', index = True, copy = False,tracking=True,)
    sale_team_id = fields.Many2one('crm.team', string = 'Sale Team', required = True,
                                ondelete = 'cascade', index = True, copy = False,tracking=True,)
    payment_term_id = fields.Many2one(comodel_name = "account.payment.term", string = "Payment Terms",tracking=True,)
    payment_method_id = fields.Many2one('account.payment.method', string ='Payment Method',tracking=True,)
    sale_user_employee_id = fields.Many2one('hr.employee', string = 'Sale Person', index = True, tracking = True, domain="[('id', 'in', sale_employee_ids)]")
    department_id = fields.Many2one('hr.department', string='Department (HR)',)
    
    @api.depends('sale_team_id')
    def _compute_sale_employee_ids(self):
        for rec in self:
            rec.sale_employee_ids = rec.sale_team_id.sale_employee_ids.ids

    @api.onchange("sale_team_id")
    def _onchange_team_id_department_id(self):
        if self.sale_team_id.department_id:
            self.department_id = self.sale_team_id.department_id.id

    sale_employee_ids = fields.Many2many('hr.employee', compute = "_compute_sale_employee_ids")