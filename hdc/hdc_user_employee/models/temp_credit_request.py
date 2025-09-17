# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError

class TempCreditRequest(models.Model):
    _inherit = 'temp.credit.request'
    _description = "Temp Credit Request"

    user_employee_id = fields.Many2one('hr.employee', string = 'Sale Person', required=True,domain="[('id', 'in', sale_employee_ids)]")
    sale_person = fields.Many2one('res.users', string = 'Sale Person User', required=False)
    
    # Salesperson
    @api.onchange("user_employee_id")
    def _onchange_user_employee_id(self):
        if self.user_employee_id.user_id:
            self.sale_person = self.user_employee_id.user_id

    @api.depends('sale_team_id')
    def _compute_sale_employee_ids(self):
        for rec in self:
            rec.sale_employee_ids = rec.sale_team_id.sale_employee_ids.ids

    sale_employee_ids = fields.Many2many('hr.employee', compute = "_compute_sale_employee_ids")