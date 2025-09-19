# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    @api.model
    def default_get(self, default_fields):
        rec = super(AccountPaymentRegister, self).default_get(default_fields)
        active_ids = self._context.get("active_ids") or self._context.get("active_id")
        active_model = self._context.get("active_model")

        # Check for selected invoices ids
        if not active_ids or active_model != "account.move":
            return rec
        invoices = (
            self.env["account.move"]
            .browse(active_ids)
            .filtered(lambda move: move.is_invoice(include_receipts=True))
        )
        for move in invoices:
            rec.update(
                {
                    "manual_currency_rate_active": move.manual_currency_rate_active,
                    "manual_currency_inverse_rate": move.manual_currency_inverse_rate,
                    "manual_currency_rate": move.manual_currency_rate,
                }
            )
        return rec

    manual_currency_inverse_rate = fields.Float(
        "Inverse Rate",
        digits=0,
        default=1,
        group_operator="avg",
        help="The currency of rate 1 to the rate of the currency.",
    )
    manual_currency_rate = fields.Float(
        "Rate",
        digits=0,
        compute="_compute_manual_rate",
        inverse="_inverse_manual_rate",
        group_operator="avg",
        help="The currency of rate 1 to the rate of the currency.",
    )
    same_currency = fields.Boolean(compute="_compute_same_currency", store=False)
    main_amount = fields.Monetary(
        string="Main Amount",
        currency_field="company_currency_id",
        readonly=False,
    )
    

    @api.onchange(
        "currency_id", "company_currency_id", "manual_currency_inverse_rate", "amount"
    )
    def calculate_main_amount_compute(self):
        """Calculate main_amount when related fields change"""
        same_currency = self.currency_id == self.company_currency_id
        if same_currency:
            self.main_amount = self.amount
        else:
            self.main_amount = self.amount * self.manual_currency_inverse_rate

    def calculate_exchange_rate_on_main_amount(self):
        if self.manual_currency_rate_active:
            amount = self.amount
            self.write({
                'manual_currency_inverse_rate': (self.main_amount / self.amount),
                'amount': amount
                })
        return {
            "name": _("Register Payment"),
            "res_id": self.id,
            "res_model": "account.payment.register",
            "view_mode": "form",
            "context": self._context,
            "target": "new",
            "type": "ir.actions.act_window",
        }

    @api.depends("currency_id", "company_currency_id")
    def _compute_same_currency(self):
        for move in self:
            move.same_currency = move.currency_id == move.company_currency_id

    @api.onchange("manual_currency_rate_active")
    def onchange_manual_currency_rate_active(self):
        if self.manual_currency_rate_active and self.manual_currency_inverse_rate == 1:
            _rate = self.currency_id._get_conversion_rate(
                self.company_currency_id,
                self.currency_id,
                self.company_id or self.env.company,
                self.payment_date or fields.Date.today(),
            )
            self.manual_currency_rate = _rate
            self._inverse_manual_rate()
        elif not self.manual_currency_rate_active:
            self.manual_currency_rate = 1.0
            self._inverse_manual_rate()

    @api.depends("manual_currency_inverse_rate")
    def _compute_manual_rate(self):
        for currency_rate in self:
            if not currency_rate.manual_currency_inverse_rate:
                currency_rate.manual_currency_inverse_rate = 1.0
            currency_rate.manual_currency_rate = (
                1.0 / currency_rate.manual_currency_inverse_rate
            )

    @api.onchange("manual_currency_rate")
    def _inverse_manual_rate(self):
        for currency_rate in self:
            if not currency_rate.manual_currency_rate:
                currency_rate.manual_currency_rate = 1.0
            currency_rate.manual_currency_inverse_rate = (
                1.0 / currency_rate.manual_currency_rate
            )

    @api.constrains("manual_currency_rate")
    def _check_manual_currency_rate(self):
        for record in self:
            if record.manual_currency_rate_active:
                if record.manual_currency_rate == 0:
                    raise Warning(
                        _("Exchange Rate Field is required , Please fill that.")
                    )
