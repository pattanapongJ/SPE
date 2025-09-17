# -*- coding: utf-8 -*-
from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_spec = fields.Many2one('res.users', string = 'Sale Spec')
    sale_manager_id = fields.Many2one("res.users", string="Sale Manager")
    user_sale_agreement = fields.Many2one('res.users', string = 'Sale Taker', default=lambda self: self.env.user)

    def default_get(self, fields_list):
        defaults = super(AccountMove, self).default_get(fields_list)
        team_id = defaults.get('team_id')
        team = self.env['crm.team'].search([('id', '=', team_id)])
        defaults['sale_manager_id'] = team.user_id.id
        return defaults