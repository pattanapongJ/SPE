# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PurchaseTeam(models.Model):
    _name = "purchase.team"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Purchase Team"
    _check_company_auto = True

    @api.model
    @api.returns('self', lambda value: value.id if value else False)
    def _get_default_purchase_team_id(self, user_id=None, domain=None):
        if not user_id:
            user_id = self.env.uid
        team_id = self.env['purchase.team'].search([
            '|', ('user_id', '=', user_id), ('member_ids', '=', user_id),
            '|', ('company_id', '=', False), ('company_id', '=', self.env.company.id)
        ], limit=1)
        if not team_id and 'default_team_id' in self.env.context:
            team_id = self.env['purchase.team'].browse(self.env.context.get('default_team_id'))
        if not team_id:
            team_id = self.env['purchase.team']
        return team_id

    active = fields.Boolean(default=True)
    name = fields.Char(string="Name", required=True)
    user_id = fields.Many2one('res.users', string="Team Leader", check_company=True)
    member_ids = fields.Many2many(
        'res.users', 'purchase_team_user_rel', 'team_id', 'user_id', string="Team Members", check_company=True,
        domain=lambda self: [('groups_id', 'in', self.env.ref('purchase.group_purchase_user').id)])
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company, index=True)
