# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    billing_period_id = fields.Many2one(comodel_name='account.billing.period', string="Billing Period")

    billing_route_id = fields.Many2one(comodel_name='account.billing.route', string="Billing Route")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):

        if self.partner_id.billing_period_id or self.partner_id.billing_period_id:
            self.billing_period_id = self.partner_id.billing_period_id.id
            self.billing_route_id = self.partner_id.billing_route_id.id
