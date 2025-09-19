# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
from datetime import datetime
    
class UsersSaleTeamHistory(models.Model):
    _name = 'users.sale.team.history'
    _description = "Users Sale Team History"

    user_id = fields.Many2one('res.users', string='User')
    team_id = fields.Many2one('crm.team', "User's Sales Team")
    team_id_date_time = fields.Datetime("Date",readonly=True,)
    member_type = fields.Selection([
        ('user_id', 'Salesperson'),
        ('sale_spec', 'Sale Spec'),
    ], string="Member Type",default='user_id')