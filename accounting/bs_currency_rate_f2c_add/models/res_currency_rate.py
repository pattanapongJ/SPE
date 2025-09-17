# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResCurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    company_rate = fields.Float(
        digits=0,
        compute="_compute_company_rate",
        inverse="_inverse_company_rate",
        group_operator="avg",
        string="Rate",
    )
    inverse_company_rate = fields.Float(
        digits=0,
        compute="_compute_inverse_company_rate",
        inverse="_inverse_inverse_company_rate",
        group_operator="avg",
        string="Inverse Rate",
    )

    @api.depends('rate', 'name', 'currency_id', 'company_id', 'currency_id.rate_ids.rate')
    @api.depends_context('company')
    def _compute_company_rate(self):
        return super(ResCurrencyRate, self)._compute_company_rate()

    @api.onchange('company_rate')
    def _inverse_company_rate(self):
        return super(ResCurrencyRate, self)._inverse_company_rate()

    @api.depends('company_rate')
    def _compute_inverse_company_rate(self):
        return super(ResCurrencyRate, self)._compute_inverse_company_rate()

    @api.onchange('inverse_company_rate')
    def _inverse_inverse_company_rate(self):
        return super(ResCurrencyRate, self)._inverse_inverse_company_rate()

