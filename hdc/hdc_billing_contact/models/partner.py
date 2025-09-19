# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    billing_place_id = fields.Many2one(comodel_name='account.billing.place', string="Billing Place")
    billing_terms_id = fields.Many2one(comodel_name='account.billing.terms', string="Billing Terms")
    payment_period_id = fields.Many2one(comodel_name='account.payment.period', string="Payment Period")

