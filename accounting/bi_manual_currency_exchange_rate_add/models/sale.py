# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import Warning


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_manual_currency_inverse_rate = fields.Float('Inverse Rate', digits=0,default=1,
                                                     group_operator="avg",
                                                     help="The currency of rate 1 to the rate of the currency.",
                                                     )
    sale_manual_currency_rate = fields.Float('Rate', digits=0,
                                             compute="_compute_manual_rate",
                                             inverse="_inverse_manual_rate",
                                             group_operator="avg",
                                             help="The currency of rate 1 to the rate of the currency.", )
    same_currency = fields.Boolean(
        compute='_compute_same_currency',
        store=False
    )

    @api.depends('currency_id', 'company_id')
    def _compute_same_currency(self):
        for move in self:
            move.same_currency = move.currency_id == move.company_id.currency_id

    @api.onchange('sale_manual_currency_rate_active')
    def onchange_manual_currency_rate_active(self):
        if self.sale_manual_currency_rate_active and self.sale_manual_currency_inverse_rate == 1:
            company_currency = self.company_id.currency_id or self.env.company.currency_id
            _rate = self.currency_id._get_conversion_rate(company_currency, self.currency_id,
                                                          self.company_id or self.env.company,
                                                          self.date_order or fields.Date.today())
            self.sale_manual_currency_rate = _rate
            self._inverse_manual_rate()
        elif not self.sale_manual_currency_rate_active:
            self.sale_manual_currency_inverse_rate = 1.0
            self._inverse_manual_rate()

    @api.depends('sale_manual_currency_inverse_rate')
    def _compute_manual_rate(self):
        for currency_rate in self:
            if not currency_rate.sale_manual_currency_inverse_rate:
                currency_rate.sale_manual_currency_inverse_rate = 1.0
            currency_rate.sale_manual_currency_rate = 1.0 / currency_rate.sale_manual_currency_inverse_rate

    @api.onchange('sale_manual_currency_rate')
    def _inverse_manual_rate(self):
        for currency_rate in self:
            if not currency_rate.sale_manual_currency_rate:
                currency_rate.sale_manual_currency_rate = 1.0
            currency_rate.sale_manual_currency_inverse_rate = 1.0 / currency_rate.sale_manual_currency_rate

    @api.constrains("sale_manual_currency_rate")
    def _check_manual_currency_rate(self):
        for record in self:
            if record.sale_manual_currency_rate_active:
                if record.sale_manual_currency_rate == 0:
                    raise Warning(_('Exchange Rate Field is required , Please fill that.'))

    def _prepare_invoice(self):
        _invoice_value = super(SaleOrder, self)._prepare_invoice()
        _invoice_value.update({
            'manual_currency_rate_active': self.sale_manual_currency_rate_active,
            'manual_currency_rate': self.sale_manual_currency_rate,
            'manual_currency_inverse_rate': self.sale_manual_currency_inverse_rate,
        })
        return _invoice_value
