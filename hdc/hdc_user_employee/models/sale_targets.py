# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _,api,fields, models
from datetime import datetime
from odoo.exceptions import UserError
    
class SaleTargets(models.Model):
    _inherit = 'sale.targets'
    
    user_employee_id = fields.Many2one('hr.employee', string = 'Salesperson', index = True, tracking = 2,domain="[('id', 'in', sale_employee_ids)]")

    @api.depends('team_id')
    def _compute_sale_employee_ids(self):
        for rec in self:
            rec.sale_employee_ids = rec.team_id.sale_employee_ids.ids

    sale_employee_ids = fields.Many2many('hr.employee', compute = "_compute_sale_employee_ids")
    user_id = fields.Many2one('res.users', string = 'Salesperson user')

    @api.onchange('team_id')
    def _team_id_onchange(self):
        domain_user_employee_id = [('id', 'in', self.team_id.sale_employee_ids.ids)]
        return {'domain': {'user_employee_id': domain_user_employee_id}}

    @api.model
    def create(self, vals):
        if vals.get("user_employee_id") == False:
            sale_target_team = self.env['sale.targets'].search([('team_id','=',vals.get("team_id")),('fiscal_year_id','=',vals.get("fiscal_year_id"))],limit=1)
            if sale_target_team:
                team_id = self.env['crm.team'].search([('id','=',vals.get("team_id"))],limit=1)
                fiscal_year_id = self.env['sh.fiscal.year'].search([('id','=',vals.get("fiscal_year_id"))],limit=1)
                raise UserError(_("You have sale target for Team [%s] with Fiscal Year [%s]") % (team_id.name, fiscal_year_id.name))
        else:
            sale_target_person = self.env['sale.targets'].search([('team_id','=',vals.get("team_id")),('fiscal_year_id','=',vals.get("fiscal_year_id")),('user_employee_id','=',vals.get("user_employee_id"))],limit=1)
            if sale_target_person:
                team_id = self.env['crm.team'].search([('id','=',vals.get("team_id"))],limit=1)
                user_employee_id = self.env['hr.employee'].search([('id','=',vals.get("user_employee_id"))],limit=1)
                fiscal_year_id = self.env['sh.fiscal.year'].search([('id','=',vals.get("fiscal_year_id"))],limit=1)
                raise UserError(_("You have sale target for Sale Person [%s] with Team [%s] and Fiscal Year [%s]") % (user_employee_id.name,team_id.name, fiscal_year_id.name))
        
        res = models.Model.create(self, vals)

        return res
    
    def write(self, vals):
        if vals.get("user_employee_id"):
            user_employee_id = vals.get("user_employee_id")
        else:
            user_employee_id = self.user_employee_id.id

        if vals.get("team_id"):
            team_id = vals.get("team_id")
        else:
            team_id = self.team_id.id

        if vals.get("fiscal_year_id"):
            fiscal_year_id = vals.get("fiscal_year_id")
        else:
            fiscal_year_id = self.fiscal_year_id.id

        if user_employee_id == False:
            sale_target_team = self.env['sale.targets'].search([('team_id','=',team_id),('fiscal_year_id','=',fiscal_year_id)],limit=1)
            if sale_target_team and sale_target_team.id != self.id:
                team = self.env['crm.team'].search([('id','=',team_id)],limit=1)
                fiscal_year = self.env['sh.fiscal.year'].search([('id','=',fiscal_year_id)],limit=1)
                raise UserError(_("You have sale target for Team [%s] with Fiscal Year [%s]") % (team.name, fiscal_year.name))
        else:
            sale_target_person = self.env['sale.targets'].search([('team_id','=',team_id),('fiscal_year_id','=',fiscal_year_id),('user_employee_id','=',user_employee_id)],limit=1)
            if sale_target_person and sale_target_person.id != self.id:
                team = self.env['crm.team'].search([('id','=',team_id)],limit=1)
                user = self.env['hr.employee'].search([('id','=',user_employee_id)],limit=1)
                fiscal_year = self.env['sh.fiscal.year'].search([('id','=',fiscal_year_id)],limit=1)
                raise UserError(_("You have sale target for Sale Person [%s] with Team [%s] and Fiscal Year [%s]") % (user.name,team.name, fiscal_year.name))
        
        res = models.Model.write(self, vals)

        return res