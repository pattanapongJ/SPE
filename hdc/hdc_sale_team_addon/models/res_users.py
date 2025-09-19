# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _,api,fields, models
from datetime import datetime

class ResUsers(models.Model):
    _inherit = 'res.users'

    sale_spec_team_id = fields.Many2one(
        'crm.team', "User's Sales Team For Sale Spec",
        help='Sales Team the user is member of Sale Spec.')
    
    sale_team_history = fields.One2many(
        'users.sale.team.history', 'user_id', string='Sale Team History')

    count_sale_team_history = fields.Integer(string='sale team history count', compute='_compute_count_sale_team_history')

    def _compute_count_sale_team_history(self):
        for rec in self:
            users_sale_team_history_ids = self.env['users.sale.team.history'].search([('user_id', '=', self.id),])
            rec.count_sale_team_history = len(users_sale_team_history_ids)    

    def action_view_users_sale_team_history(self):
        return {
            'name': _('Users Sale Team History'),
            'view_mode': 'tree,form',
            'res_model': 'users.sale.team.history',
            'type': 'ir.actions.act_window',
            'context': {'create': False, 'delete': False},
            'domain': [('id','in', self.sale_team_history.ids)],
            'target': 'current',
        }