# -*- coding: utf-8 -*-
from odoo import api,models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_user_employee_id = fields.Many2one('hr.employee', string = 'Salesperson', index = True, tracking = True,domain="[('id', 'in', sale_employee_ids)]")
    sale_spec_employee = fields.Many2one('hr.employee', string = 'Sale Spec',domain="[('id', 'in', sale_spec_employee_ids)]")
    sale_manager_employee_id = fields.Many2one("hr.employee", string="Sale Manager",domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    user_sale_agreement_employee = fields.Many2one('hr.employee', string = 'Sale Taker',domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    department_id = fields.Many2one('hr.department', 'Department (HR)', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    invoice_user_id = fields.Many2one('res.users', string = 'Salesperson user')
    sale_spec = fields.Many2one('res.users', string = 'Sale Spec user')
    sale_manager_id = fields.Many2one('res.users', string = 'Sale Manager user')
    user_sale_agreement = fields.Many2one('res.users', string = 'Sale Taker user')

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

    # Salesperson
    @api.onchange("invoice_user_employee_id")
    def _onchange_invoice_user_employee_id(self):
        if self.invoice_user_employee_id.user_id:
            self.invoice_user_id = self.invoice_user_employee_id.user_id

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