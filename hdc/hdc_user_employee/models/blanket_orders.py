# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from collections import defaultdict
import re

class BlanketOrder(models.Model):
    _inherit = "sale.blanket.order"
    
    def _default_employee(self):
        employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id), ("company_id", "=", self.env.user.company_id.id)], limit=1)
        if not employee_id:
            employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)], limit=1)
        return employee_id.id
    
    user_employee_id = fields.Many2one('hr.employee', string = 'Salesperson', index = True, tracking = 2,domain="[('id', 'in', sale_employee_ids)]")
    team_department_id = fields.Many2one(related='team_id.department_id')
    sale_spec_employee = fields.Many2one('hr.employee', string = 'Sale Spec',domain="[('is_sale_spec','=',True),('department_id','=', team_department_id)]")
    sale_manager_employee_id = fields.Many2one("hr.employee", string="Sale Manager")
    administrator_employee = fields.Many2one('hr.employee', string = 'Sale Taker',default=lambda self: self._default_employee())
    department_id = fields.Many2one('hr.department', 'Department (HR)')

    user_id = fields.Many2one('res.users', string = 'Salesperson user')
    sale_spec = fields.Many2one('res.users', string = 'Sale Spec user')
    sale_manager_id = fields.Many2one('res.users', string = 'Sale Manager user')
    administrator = fields.Many2one('res.users', string = 'Sale Taker user')

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
    @api.onchange("administrator_employee")
    def _onchange_administrator_employee(self):
        if self.administrator_employee.user_id:
            self.administrator = self.administrator_employee.user_id

    @api.onchange('partner_id')
    def onchange_partner_id_check_credit_limit(self):
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
            
    def _get_fields_to_copy_from_quotation(self):
        res = super()._get_fields_to_copy_from_quotation()
        res.update({
            'user_employee_id': self.ref_sale_id.user_employee_id,
            'sale_spec_employee': self.ref_sale_id.sale_spec_employee,
            'sale_manager_employee_id': self.ref_sale_id.sale_manager_employee_id,
            'administrator_employee': self.ref_sale_id.user_sale_agreement_employee,
            'department_id': self.ref_sale_id.department_id,
        })
        return res