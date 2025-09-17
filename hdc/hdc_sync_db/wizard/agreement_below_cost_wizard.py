# -*- coding: utf-8 -*-

from odoo import api, fields, models


# Define your wizard model
class AgreementBelowCostWizard(models.TransientModel):
    _name = "agreement.below.cost.wizard"

    sale_agreement_id = fields.Many2one("sale.blanket.order", string="Sale Agreement ID", required=True)

    message = fields.Text(
        string="Message", default=""
    )

    def action_confirm_wizard(self):

        self.sale_agreement_id.is_confirm_below_cost = True

        self.sale_agreement_id.action_confirm()
        return {"type": "ir.actions.act_window_close"}
