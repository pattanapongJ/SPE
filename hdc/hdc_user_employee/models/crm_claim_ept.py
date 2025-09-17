# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import json
from odoo.tools import date_utils
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context

class CrmClaimEpt(models.Model):
    _inherit = "crm.claim.ept"
    
    def _default_employee(self):
        employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id), ("company_id", "=", self.env.user.company_id.id)], limit=1)
        if not employee_id:
            employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)], limit=1)
        return employee_id.id

    receive_by = fields.Many2one('res.users', string='Receive By user', tracking=True,
                              default=lambda self: self.env.user)
    receive_by_employee = fields.Many2one('hr.employee', string='Receive By', tracking=True,
                              default=lambda self: self._default_employee())
    
    sale_person_id = fields.Many2one('res.users', string='Sale Person user',
                              default=lambda self: self.env.user)
    sale_person_employee_id = fields.Many2one('hr.employee', string='Sale Person',
                              default=lambda self: self._default_employee())
    
    sale_spec = fields.Many2one('res.users', string = 'Sale Spec')
    sale_spec_employee = fields.Many2one('hr.employee', string = 'Sale Spec')    
    
    user_id = fields.Many2one('res.users', string='Responsible user', tracking=True,
                              default=lambda self: self.env.user)
    user_employee_id = fields.Many2one('hr.employee', string='Responsible', tracking=True,
                              default=lambda self: self._default_employee())
    
    @api.onchange("receive_by_employee")
    def _onchange_receive_by_employee(self):
        if self.receive_by_employee.user_id:
            self.receive_by = self.receive_by_employee.user_id

    @api.onchange("sale_person_employee_id")
    def _onchange_sale_person_employee_id(self):
        if self.sale_person_employee_id.user_id:
            self.sale_person_id = self.sale_person_employee_id.user_id

    @api.onchange("sale_spec_employee")
    def _onchange_sale_spec_employee(self):
        if self.sale_spec_employee.user_id:
            self.sale_spec = self.sale_spec_employee.user_id

    @api.onchange("user_employee_id")
    def _onchange_user_employee_id(self):
        if self.user_employee_id.user_id:
            self.user_id = self.user_employee_id.user_id

class PurchaseCrmClaimEpt(models.Model):
    _inherit = "purchase.crm.claim.ept"

    def _default_employee(self):
        employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id), ("company_id", "=", self.env.user.company_id.id)], limit=1)
        if not employee_id:
            employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)], limit=1)
        return employee_id.id

    receive_by = fields.Many2one('res.users', string='Receive By user', tracking=True,
                              default=lambda self: self.env.user)
    receive_by_employee = fields.Many2one('hr.employee', string='Receive By', tracking=True,
                              default=lambda self: self._default_employee())

    user_id = fields.Many2one('res.users', string='Responsible user', tracking=True,
                              default=lambda self: self.env.user)
    user_employee_id = fields.Many2one('hr.employee', string='Responsible', tracking=True,
                              default=lambda self: self._default_employee())
    
    @api.onchange("receive_by_employee")
    def _onchange_receive_by_employee(self):
        if self.receive_by_employee.user_id:
            self.receive_by = self.receive_by_employee.user_id

    @api.onchange("user_employee_id")
    def _onchange_user_employee_id(self):
        if self.user_employee_id.user_id:
            self.user_id = self.user_employee_id.user_id

    