# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    billing_period_id = fields.Many2one(comodel_name='account.billing.period', string="Billing Period")

    billing_route_id = fields.Many2one(comodel_name='account.billing.route', string="Billing Route")

