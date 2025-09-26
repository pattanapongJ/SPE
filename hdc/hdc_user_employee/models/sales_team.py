from datetime import date

from odoo import api, fields, models, _
from datetime import datetime

class CrmTeam(models.Model):
    _inherit = "crm.team"

    department_id = fields.Many2one('hr.department', 'Department')
    user_employee_id = fields.Many2one('hr.employee', string='Team Leader',domain="[('department_id', '=', department_id)]", check_company=False)
    sale_employee_ids = fields.One2many(
        'hr.employee', 'sale_team_id', string='Sale Members',
        check_company=False,domain="[('department_id', '=', department_id)]",)
    sale_spec_employee_ids = fields.One2many(
        'hr.employee', 'sale_spec_team_id', string='Sale Spec Members',
        check_company=False,domain="[('department_id', '=', department_id),('is_sale_spec', '=',True)]",)
    user_id = fields.Many2one('res.users', string = 'Team Leader user', check_company=False)

    @api.onchange("user_employee_id")
    def _onchange_user_employee_id(self):
        if self.user_employee_id.user_id:
            self.user_id = self.user_employee_id.user_id

    def update_employee_member(self):
        for rec in self:
            if rec.department_id:  
                employee_ids = self.env['hr.employee'].search([('department_id', '=', rec.department_id.id)])
                for sale_employee in rec.sale_employee_ids:
                    if (sale_employee.department_id.id != rec.department_id.id and sale_employee.sale_team_id.id == rec.id):
                        sale_employee.sale_team_id = False
            
                for employee in employee_ids:
                    if employee.department_id.id == rec.department_id.id and employee.sale_team_id.id != rec.id:
                        employee.sale_team_id = rec.id
                        employee_sale_team_history = rec.env["employee.sale.team.history"].create({
                                "user_employee_id": employee.id,
                                "team_id": rec.id,
                                "team_id_date_time":datetime.now(),
                                "member_type":"sale_person",})
            else:
                for sale_employee in rec.sale_employee_ids:
                    sale_employee.sale_team_id = False

    def write(self, vals):
        sale_employee_ids = vals.get("sale_employee_ids")
        sale_spec_employee_ids = vals.get("sale_spec_employee_ids")
        if sale_employee_ids:
            if sale_employee_ids[0][2] != False:
                for employee in sale_employee_ids[0][2]:
                    employee_id = self.env['hr.employee'].search([('id', '=', employee)])
                    if employee_id:
                        if employee_id.sale_team_id.id != self.id:
                            employee_sale_team_history = self.env["employee.sale.team.history"].create({
                                "user_employee_id": employee_id.id,
                                "team_id": self.id,
                                "team_id_date_time":datetime.now(),
                                "member_type":"sale_person",})
        
        if sale_spec_employee_ids:
            if sale_spec_employee_ids[0][2] != False:
                for employee in sale_spec_employee_ids[0][2]:
                    employee_id = self.env['hr.employee'].search([('id', '=', employee)])
                    if employee_id:
                        if employee_id.sale_spec_team_id.id != self.id:
                            employee_sale_team_history = self.env["employee.sale.team.history"].create({
                                "user_employee_id": employee_id.id,
                                "team_id": self.id,
                                "team_id_date_time":datetime.now(),
                                "member_type":"sale_spec",})
                       
        res = super(CrmTeam, self).write(vals)
        return res
