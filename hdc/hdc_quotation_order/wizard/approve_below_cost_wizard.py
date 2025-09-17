# -*- coding: utf-8 -*-

from odoo import api, fields, models


# Define your wizard model
class ApproveBelowCostWizard(models.TransientModel):
    _name = "approve.below.cost.wizard"

    quotation_order_id = fields.Many2one("quotation.order", string="Quotation Order ID", required=True)

    message = fields.Text(
        string="Message", default=""
    )

    def action_approve_wizard(self):
        self.quotation_order_id.is_approve_below_cost = True
        self.quotation_order_id.action_approved()
        return {"type": "ir.actions.act_window_close"}
