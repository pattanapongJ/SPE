# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.misc import formatLang, get_lang
import re

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _default_employee(self):
        employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id), ("company_id", "=", self.env.user.company_id.id)], limit=1)
        if not employee_id:
            employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)], limit=1)
        return employee_id.id
    
    user_employee_id = fields.Many2one('hr.employee', string = 'Salesperson', index = True, tracking = 2,domain="[('id', 'in', sale_employee_ids)]")
    team_department_id = fields.Many2one(related='team_id.department_id')
    sale_spec_employee = fields.Many2one('hr.employee', string = 'Sale Spec',domain="[('is_sale_spec','=',True),('department_id','=', team_department_id)]")
    sale_manager_employee_id = fields.Many2one("hr.employee", string="Sale Manager")
    user_sale_agreement_employee = fields.Many2one('hr.employee', string = 'Sale Taker',default=lambda self: self._default_employee())
    department_id = fields.Many2one('hr.department', 'Department (HR)')

    user_id = fields.Many2one('res.users', string = 'Salesperson user')
    sale_spec = fields.Many2one('res.users', string = 'Sale Spec user')
    sale_manager_id = fields.Many2one('res.users', string = 'Sale Manager user')
    user_sale_agreement = fields.Many2one('res.users', string = 'Sale Taker user')
    requestor_emp_employee = fields.Many2one('hr.employee', string='Requestor',default=lambda self: self._default_employee())
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

    @api.onchange("team_id")
    def _onchange_team_id_user_employee(self):
        self.sale_manager_employee_id = self.team_id.user_employee_id
        self.department_id = self.team_id.department_id
        if self.partner_id:
            if self.env.user.employee_id in self.team_id.sale_employee_ids:
                self.user_employee_id = self.env.user.employee_id
            else:
                self.user_employee_id = False
            # if self.user_employee_id in self.sale_spec_employee_ids:
            #     self.sale_spec_employee = self.user_employee_id
            # else:
            #     employee_id = self.env['hr.employee'].search([('is_sale_spec', '=', True)], limit=1)
            #     if employee_id:
            #         self.sale_spec_employee = employee_id

    # Salesperson
    @api.onchange("user_employee_id")
    def _onchange_user_employee_id(self):
        if self.user_employee_id.user_id:
            self.user_id = self.user_employee_id.user_id
            # Finance Dimension 2
            _dimension_datas = self.env.ref('bs_finance_dimension.bs_dimension_2').finance_dimension_ids.filtered(
                lambda x: x.res_id == self.user_employee_id.user_id.id)
            if _dimension_datas:
                self.finance_dimension_2_id = _dimension_datas[0]
            else:
                self.finance_dimension_2_id = None
        customer_credit_id = self.env["customer.credit.limit"].search([('partner_id', '=', self.partner_id.id)])
        if customer_credit_id:
            credit_line_person_id = self.env["credit.limit.sale.person.line"].search([('credit_id', '=', customer_credit_id.credit_id.id),('sale_user_employee_id','=',self.user_employee_id.id)])
            if credit_line_person_id:
                self.payment_term_id = credit_line_person_id.payment_term_id.id
                self.payment_method_id = credit_line_person_id.payment_method_id.id
                self.billing_period_id = credit_line_person_id.billing_period_id.id
                self.payment_period_id = credit_line_person_id.payment_period_id.id

        # if self.user_employee_id in self.sale_spec_employee_ids:
        #     self.sale_spec_employee = self.user_employee_id
        # else:
        #     employee_id = self.env['hr.employee'].search([('is_sale_spec', '=', True)], limit=1)
        #     if employee_id:
        #         self.sale_spec_employee = employee_id

    # Sale Spec
    @api.onchange("sale_spec_employee")
    def _onchange_sale_spec_employee(self):
        if self.sale_spec_employee.user_id:
            self.sale_spec = self.sale_spec_employee.user_id

    # Sale Manager
    @api.onchange("sale_manager_employee_id")
    def _onchange_sale_manager_employee_id(self):
        if self.sale_manager_employee_id.user_id:
            self.sale_manager_id = self.sale_manager_employee_id.user_id

    # Sale Taker
    @api.onchange("user_sale_agreement_employee")
    def _onchange_user_sale_agreement_employee(self):
        if self.user_sale_agreement_employee.user_id:
            self.user_sale_agreement = self.user_sale_agreement_employee.user_id

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        if self.user_employee_id:
            res["invoice_user_employee_id"] = self.user_employee_id.id
        if self.sale_spec_employee:
            res["sale_spec_employee"] = self.sale_spec_employee.id
        if self.sale_manager_employee_id:
            res["sale_manager_employee_id"] = self.sale_manager_employee_id.id
        if self.user_sale_agreement_employee:
            res["user_sale_agreement_employee"] = self.user_sale_agreement_employee.id
        if self.department_id:
            res["department_id"] = self.department_id.id
        return res
    
    @api.onchange('partner_id')
    def onchange_partner_id_team_id_credit_limit(self):
        customer_credit_id = self.env["customer.credit.limit"].search([('partner_id', '=', self.partner_id.id)])
        # if customer_credit_id.credit_id.credit_line:
        #     credit_line = customer_credit_id.credit_id.credit_line
        #     if len(credit_line) > 0:
        #         self.team_id = credit_line[0].sale_team_id
        #         self.user_employee_id = credit_line[0].sale_user_employee_id

        if self.partner_id.credit_limit_on_hold == True:
            return {
                    'warning': {'title': "Customer On Hold", 
                                'message': 
                                "Customer have been on hold. Please contact administration for further guidance"
                                },
                }
        
        if customer_credit_id:
            credit_team_remain = 0
            sale_team_id = False
            if customer_credit_id:
                sale_team_id = customer_credit_id.credit_id.credit_line.filtered(lambda l: l.sale_team_id == self.team_id)
                if sale_team_id:
                    credit_team_remain = sale_team_id.credit_remain

            if self.partner_id.cash_limit <= 0 or credit_team_remain <= 0:
                partner_id = self.partner_id

                exceeded_amount_team = credit_team_remain - self.amount_total
                exceeded_amount_team = "{:.2f}".format(exceeded_amount_team)
                exceeded_amount_team = float(exceeded_amount_team)
                
                return {
                    'warning': {'title': "Credit Limit Warning", 
                                'message': 
                                "Customer: %s \nCredit Remain: %.2f  \nCash Limit: %.2f \nExceeded Amount (Credit): %.2f "  
                                % (partner_id.name, credit_team_remain ,partner_id.cash_limit ,exceeded_amount_team),
                                },
                }
            
    def create_credit_request(self):
        action = {
            'name': _('Temp Credit Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'temp.credit.request',
            "views": [(self.env.ref("hdc_creditlimit_saleteam.view_temp_credit_request_form").id, "form")],
            'view_mode': 'form',
            'context': {
                'default_order_no': self.id,
                'default_partner_id': self.partner_id.id,
                'default_sale_person': self.user_id.id,
                'default_user_employee_id': self.user_employee_id.id,
                'default_sale_team_id': self.team_id.id,
                },
            }
        return action

            
    def create_temp_credit_request(self):
        for order in self:
            self.env['temp.credit.request'].create({
                'order_no': order.id,
                'partner_id': order.partner_id.id,
                'user_employee_id': order.user_employee_id.id,
                'sale_team_id': order.team_id.id,
            })