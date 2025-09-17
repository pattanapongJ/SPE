# -*- coding: utf-8 -*-

from odoo import api, fields, models


# Define your wizard model
class BelowCostWarningWizardBooth(models.TransientModel):
    _name = "below.cost.warning.wizard.booth"

    sale_order_id = fields.Many2one("sale.order", string="Sale Order ID", required=True)

    message = fields.Text(
        string="Message", default=""
    )

    def action_confirm_wizard(self):

        self.sale_order_id.is_confirm_below_cost = True

        # self.sale_order_id.action_sale_ok2()

        return {"type": "ir.actions.act_window_close"}
