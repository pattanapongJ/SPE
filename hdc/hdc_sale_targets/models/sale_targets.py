# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _,api,fields, models
from datetime import datetime
from odoo.exceptions import UserError
    
class SaleTargets(models.Model):
    _name = 'sale.targets'
    _description = "Sale Targets for Sales Teams/Sales Person"

    team_id = fields.Many2one('crm.team', "Sale Team")
    user_id = fields.Many2one('res.users', string='Sale Person',domain="[('id', 'in', member_ids)]")
    fiscal_year_id = fields.Many2one('sh.fiscal.year', string="Fiscal Year")
    target_team = fields.Float(string='Target by Team')
    target_sales = fields.Float(string='Target by Sales')

    @api.depends('team_id')
    def _compute_member_ids(self):
        for rec in self:
            rec.member_ids = rec.team_id.member_ids.ids
    member_ids = fields.Many2many('res.users', compute = "_compute_member_ids")

    @api.onchange('team_id')
    def _team_id_onchange(self):
        domain_user_id = [('id', 'in', self.team_id.member_ids.ids)]
        return {'domain': {'user_id': domain_user_id}}
    
    @api.onchange('team_id','fiscal_year_id')
    def _team_id_fiscal_year_id_onchange(self):
        sale_target = self.env['sale.targets'].search([('team_id','=',self.team_id.id),('fiscal_year_id','=',self.fiscal_year_id.id)],limit=1)
        if sale_target:
            self.target_team = sale_target.target_team
        else:
            self.target_team = False

    @api.model
    def create(self, vals):
        if vals.get("user_id") == False:
            sale_target_team = self.env['sale.targets'].search([('team_id','=',vals.get("team_id")),('fiscal_year_id','=',vals.get("fiscal_year_id"))],limit=1)
            if sale_target_team:
                team_id = self.env['crm.team'].search([('id','=',vals.get("team_id"))],limit=1)
                fiscal_year_id = self.env['sh.fiscal.year'].search([('id','=',vals.get("fiscal_year_id"))],limit=1)
                raise UserError(_("You have sale target for Team [%s] with Fiscal Year [%s]") % (team_id.name, fiscal_year_id.name))
        else:
            sale_target_person = self.env['sale.targets'].search([('team_id','=',vals.get("team_id")),('fiscal_year_id','=',vals.get("fiscal_year_id")),('user_id','=',vals.get("user_id"))],limit=1)
            if sale_target_person:
                team_id = self.env['crm.team'].search([('id','=',vals.get("team_id"))],limit=1)
                user_id = self.env['res.users'].search([('id','=',vals.get("user_id"))],limit=1)
                fiscal_year_id = self.env['sh.fiscal.year'].search([('id','=',vals.get("fiscal_year_id"))],limit=1)
                raise UserError(_("You have sale target for Sale Person [%s] with Team [%s] and Fiscal Year [%s]") % (user_id.name,team_id.name, fiscal_year_id.name))
        
        res = super(SaleTargets, self).create(vals)

        return res
    
    def write(self, vals):
        if vals.get("user_id"):
            user_id = vals.get("user_id")
        else:
            user_id = self.user_id.id

        if vals.get("team_id"):
            team_id = vals.get("team_id")
        else:
            team_id = self.team_id.id

        if vals.get("fiscal_year_id"):
            fiscal_year_id = vals.get("fiscal_year_id")
        else:
            fiscal_year_id = self.fiscal_year_id.id

        if user_id == False:
            sale_target_team = self.env['sale.targets'].search([('team_id','=',team_id),('fiscal_year_id','=',fiscal_year_id)],limit=1)
            if sale_target_team and sale_target_team.id != self.id:
                team = self.env['crm.team'].search([('id','=',team_id)],limit=1)
                fiscal_year = self.env['sh.fiscal.year'].search([('id','=',fiscal_year_id)],limit=1)
                raise UserError(_("You have sale target for Team [%s] with Fiscal Year [%s]") % (team.name, fiscal_year.name))
        else:
            sale_target_person = self.env['sale.targets'].search([('team_id','=',team_id),('fiscal_year_id','=',fiscal_year_id),('user_id','=',user_id)],limit=1)
            if sale_target_person and sale_target_person.id != self.id:
                team = self.env['crm.team'].search([('id','=',team_id)],limit=1)
                user = self.env['res.users'].search([('id','=',user_id)],limit=1)
                fiscal_year = self.env['sh.fiscal.year'].search([('id','=',fiscal_year_id)],limit=1)
                raise UserError(_("You have sale target for Sale Person [%s] with Team [%s] and Fiscal Year [%s]") % (user.name,team.name, fiscal_year.name))
        
        res = super(SaleTargets, self).write(vals)

        return res