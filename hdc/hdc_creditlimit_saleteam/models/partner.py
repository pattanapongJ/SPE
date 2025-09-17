# -*- coding: utf-8 -*-
from odoo import models, fields,api

class ResPartner(models.Model):
    _inherit= 'res.partner'

    credit_type = fields.Selection([
        ('new', 'New Customer'),
        ('credit', 'Group Credit limit')
    ], string='Credit Type',default='new',required=True,copy=False)
    credit_limit_on_hold  = fields.Boolean('Credit limit on hold', default=False)
    credit_limit = fields.Float('Credit Limit', default=lambda self: self._default_credit_limit(),compute='_compute_credit_limit')
    credit_limit_show = fields.Float('Credit Limit', default=lambda self: self._default_credit_limit(),compute='_compute_credit_limit')
    cash_limit = fields.Float('Cash Limit', default=lambda self: self._default_credit_limit(),compute='_compute_credit_limit')
    cash_limit_show = fields.Float('Cash Limit', default=lambda self: self._default_credit_limit(),compute='_compute_credit_limit')
    property_payment_term_id = fields.Many2one(
        'account.payment.term',
        company_dependent=True,
        string='Customer Payment Terms',
        domain="[('company_id', 'in', [current_company_id, False])]",
        default=lambda self: self._default_payment_term(),
        help="This payment term will be used instead of the default one for sales orders and customer invoices"
    )
    remark_on_hold = fields.Text("Remark On Hold",tracking=True,)
    @api.model
    def _default_payment_term(self):
        # ค้นหาเงื่อนไขการชำระเงินที่มีฟิลด์ is_cash เป็น True
        cash_payment_term = self.env['account.payment.term'].search([('is_cash', '=', True)], limit=1)
        return cash_payment_term.id if cash_payment_term else False
    
    @api.model
    def _default_credit_limit(self):
        return float(self.env['ir.config_parameter'].sudo().get_param('hdc_creditlimit_saleteam.default_credit_limit', default=40000.00))

    def write(self, vals):
        print("DEBUG: write called with vals:", vals)
        if vals.get("credit_type") == 'new':
            print("DEBUG: credit_type is 'new'")
            partner_customers = self.env['customer.credit.limit'].search([('partner_id', 'in', self.ids)])
            print("DEBUG: partner_customers found:", partner_customers)
            vals["credit_limit_on_hold"] = False
            if partner_customers:
                print("DEBUG: Unlinking partner_customers")
                partner_customers.sudo().with_context(skip_partner_write=True).unlink()
        result = super(ResPartner, self).write(vals)
        print("DEBUG: super write result:", result)
        return result

    def _compute_credit_limit(self):
        for rec in self:
            partner_customers = self.env['customer.credit.limit'].search([('partner_id', '=', rec.id)])
            partner_customers_cash_new = self.env['customer.cash.limit'].search([('partner_id', '=', rec.id)])
            if partner_customers:
                rec.credit_type = "credit"
                rec.credit_limit = partner_customers.credit_id.credit_limit_remain_total
                rec.credit_limit_show = partner_customers.credit_id.total_credit
                rec.cash_limit = partner_customers_cash_new.cash_remain
                rec.cash_limit_show = partner_customers_cash_new.cash_limit
            elif partner_customers_cash_new:
                default_credit_limit = float(self.env['ir.config_parameter'].sudo().get_param('hdc_creditlimit_saleteam.default_credit_limit', default=40000.00))
                rec.credit_type = "new"
                rec.credit_limit = default_credit_limit
                rec.credit_limit_show = default_credit_limit
                rec.cash_limit = partner_customers_cash_new.cash_remain
                rec.cash_limit_show = partner_customers_cash_new.cash_limit
            else:
                default_credit_limit = float(self.env['ir.config_parameter'].sudo().get_param('hdc_creditlimit_saleteam.default_credit_limit', default=40000.00))
                rec.credit_limit = default_credit_limit
                rec.credit_limit_show = default_credit_limit
                rec.cash_limit = default_credit_limit
                rec.cash_limit_show = default_credit_limit
    
    @api.onchange('credit_type')
    def _onchange_credit_type(self):
        for rec in self:
            if rec.credit_type == 'new':
                cash_payment_term = rec.env['account.payment.term'].search([('is_cash', 'in', True)],limit=1)
                if cash_payment_term:
                    rec.property_payment_term_id = cash_payment_term.id
            rec._compute_credit_limit()

    @api.model
    def create(self, vals):
        partner = super().create(vals)
        partner._create_cash_limit()
        return partner

    def _create_cash_limit(self):
        for partner in self:
            if not self.env['customer.cash.limit'].search([('partner_id', '=', partner.id)]):
                self.env['customer.cash.limit'].create({
                    'partner_id': partner.id,
                })

    def create_partner_cash_limit(self):
        partner_all = self.env['res.partner'].search([])        
        for partner in partner_all:
            if not self.env['customer.cash.limit'].search([('partner_id', '=', partner.id)]):
                self.env['customer.cash.limit'].create({
                    'partner_id': partner.id,
                })


    def action_open_cash_limit(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cash Limit',
            'res_model': 'customer.cash.limit',
            'view_mode': 'tree',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'create': False,
                'edit': False,
                'delete': False,
            },
            'views': [(False, 'tree')],
            'target': 'current',
        }