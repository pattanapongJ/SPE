# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResCurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    company_rate = fields.Float(
        digits=0,
        compute="_compute_company_rate",
        inverse="_inverse_company_rate",
        group_operator="avg",
        string="Unit to Main",
    )
    inverse_company_rate = fields.Float(
        digits=0,
        compute="_compute_inverse_company_rate",
        inverse="_inverse_inverse_company_rate",
        group_operator="avg",
        string="Main to Unit",
    )

    @api.depends('rate', 'name', 'currency_id', 'company_id', 'currency_id.rate_ids.rate')
    @api.depends_context('company')
    def _compute_company_rate(self):
        last_rate = self.env['res.currency.rate']._get_last_rates_for_companies(self.company_id | self.env.company)
        for currency_rate in self:
            company = currency_rate.company_id or self.env.company
            currency_rate.company_rate = (currency_rate.rate or self._get_latest_rate().rate or 1.0) / last_rate[
                company]

    @api.onchange('company_rate')
    def _inverse_company_rate(self):
        last_rate = self.env['res.currency.rate']._get_last_rates_for_companies(self.company_id | self.env.company)
        for currency_rate in self:
            company = currency_rate.company_id or self.env.company
            currency_rate.rate = currency_rate.company_rate * last_rate[company]

    @api.depends('company_rate')
    def _compute_inverse_company_rate(self):
        for currency_rate in self:
            currency_rate.inverse_company_rate = 1.0 / currency_rate.company_rate

    @api.onchange('inverse_company_rate')
    def _inverse_inverse_company_rate(self):
        for currency_rate in self:
            currency_rate.company_rate = 1.0 / currency_rate.inverse_company_rate

    def _get_latest_rate(self):
        return self.currency_id.rate_ids.filtered(lambda x: (
            x.rate
            and x.company_id == (self.company_id or self.env.company)
            and x.name < (self.name or fields.Date.today())
        )).sorted('name')[-1:]

    def _get_last_rates_for_companies(self, companies):
        return {
            company: company.currency_id.rate_ids.filtered(lambda x: (
                    x.rate
                    and x.company_id == company or not x.company_id
            )).sorted('name')[-1:].rate or 1
            for company in companies
        }