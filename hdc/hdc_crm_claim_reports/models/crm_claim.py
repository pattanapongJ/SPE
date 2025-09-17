from odoo import api, fields, models


class CrmClaim(models.Model):
    _inherit = "crm.claim"

    def get_model_name(self,data):
        model_name = self.model_ref_id._name
        if model_name == "sale.order":
            model_name = "Sales Orders"
        else:
            model_name = self.model_ref_id._description
        return model_name

    def print(self):
        self.ensure_one()
        return {
                "name": "Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.crm.claim.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_state": self.stage_id,
                            "default_crm_claim_id": self.id,},
            }
