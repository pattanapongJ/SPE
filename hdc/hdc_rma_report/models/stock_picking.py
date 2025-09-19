# Copyright 2018 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import _, api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def print_rma_list(self):
        self.ensure_one()
        return {
                "name": "Report RMA",
                "type": "ir.actions.act_window",
                "res_model": "wizard.rma.report.list",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_state": self.claim_id.state,
                            "default_rma_id": self.claim_id.id},
            }
