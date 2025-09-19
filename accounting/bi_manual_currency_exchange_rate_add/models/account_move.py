from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.exceptions import Warning


class AccountMove(models.Model):
    _inherit = 'account.move'

    manual_currency_inverse_rate = fields.Float('Inverse Rate', digits=0,default=1,
                                                group_operator="avg",
                                                help="The currency of rate 1 to the rate of the currency.",
                                                )
    manual_currency_rate = fields.Float('Rate', digits=0,
                                        compute="_compute_manual_rate",
                                        inverse="_inverse_manual_rate",
                                        group_operator="avg",
                                        help="The currency of rate 1 to the rate of the currency.", )
    same_currency = fields.Boolean(
        compute='_compute_same_currency',
        store=False
    )

    @api.depends('currency_id', 'company_currency_id')
    def _compute_same_currency(self):
        for move in self:
            move.same_currency = move.currency_id == move.company_currency_id


    @api.onchange('manual_currency_rate_active')
    def onchange_manual_currency_rate_active(self):
        if self.manual_currency_rate_active and self.manual_currency_inverse_rate==1:
            _rate = self.currency_id._get_conversion_rate(self.company_currency_id, self.currency_id,
                                                          self.company_id or self.env.company,
                                                          self.date or fields.Date.today())
            self.manual_currency_rate = _rate
            self._inverse_manual_rate()

        elif not self.manual_currency_rate_active:
            self.manual_currency_rate = 1.0
            self._inverse_manual_rate()
        self.line_ids._onchange_amount_currency()

    @api.depends('manual_currency_inverse_rate')
    def _compute_manual_rate(self):
        for currency_rate in self:
            if not currency_rate.manual_currency_inverse_rate:
                currency_rate.manual_currency_inverse_rate = 1.0
            currency_rate.manual_currency_rate = 1.0 / currency_rate.manual_currency_inverse_rate

    @api.onchange('manual_currency_rate')
    def _inverse_manual_rate(self):
        for currency_rate in self:
            if not currency_rate.manual_currency_rate:
                currency_rate.manual_currency_rate = 1.0
            currency_rate.manual_currency_inverse_rate = 1.0 / currency_rate.manual_currency_rate

    @api.onchange('manual_currency_rate_active','manual_currency_inverse_rate','manual_currency_rate')
    def onchange_manual_currency_inverse_rate(self):
        self.line_ids._onchange_amount_currency()

