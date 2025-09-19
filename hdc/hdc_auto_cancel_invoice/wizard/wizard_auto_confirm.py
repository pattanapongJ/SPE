# -*- coding: utf-8 -*-

from odoo import api, fields, models


class WizardTmsDay(models.TransientModel):
    _name = "wizard.auto.confirm"

    name = fields.Char(default="")

    account_id = fields.Many2one('account.move')


    def confirm_ok(self):
        self.account_id.cancel_entry_auto()
        return {"type": "ir.actions.act_window_close"}

    def confirm_cancel(self):
        return {"type": "ir.actions.act_window_close"}

