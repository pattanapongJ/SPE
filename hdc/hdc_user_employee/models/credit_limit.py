# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError


class CreditLimitSaleLine(models.Model):
    _inherit = 'credit.limit.sale.line'

    sale_user_employee_id = fields.Many2one('hr.employee', string = 'Sale Person', index = True, tracking = True, domain="[('id', 'in', sale_employee_ids)]")
    company_id = fields.Many2one(related='sale_team_id.company_id',string="Company",store=True)
    department_id = fields.Many2one(related='sale_team_id.department_id', string='Department (HR)',)
    
    @api.depends('sale_team_id')
    def _compute_sale_employee_ids(self):
        for rec in self:
            rec.sale_employee_ids = rec.sale_team_id.sale_employee_ids.ids

    sale_employee_ids = fields.Many2many('hr.employee', compute = "_compute_sale_employee_ids")

    @api.onchange("sale_user_employee_id")
    def _onchange_sale_user_employee_id(self):
        if self.sale_user_employee_id.user_id:
            self.sale_user_id = self.sale_user_employee_id.user_id