# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    billing_place_id = fields.Many2one(comodel_name='account.billing.place', string="Billing Place")
    billing_terms_id = fields.Many2one(comodel_name='account.billing.terms', string="Billing Terms")
    payment_period_id = fields.Many2one(comodel_name='account.payment.period', string="Payment Period")

    @api.onchange('partner_id')
    def _onchange_partner_id_billing_contact(self):

        if self.partner_id.billing_place_id:
            self.billing_place_id = self.partner_id.billing_place_id.id
        if self.partner_id.billing_terms_id:
            self.billing_terms_id = self.partner_id.billing_terms_id.id
        if self.partner_id.payment_period_id:
            self.payment_period_id = self.partner_id.payment_period_id.id