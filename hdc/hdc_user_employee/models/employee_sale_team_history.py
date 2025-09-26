# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
from datetime import datetime
    
class EmployeeSaleTeamHistory(models.Model):
    _name = 'employee.sale.team.history'
    _description = "Employee Sale Team History"

    user_employee_id = fields.Many2one('hr.employee', string='Employee')
    team_id = fields.Many2one('crm.team', "Employee's Sales Team")
    team_id_date_time = fields.Datetime("Date",readonly=True,)
    member_type = fields.Selection([
        ('sale_person', 'Salesperson'),
        ('sale_spec', 'Sale Spec'),
    ], string="Member Type",default='sale_person')