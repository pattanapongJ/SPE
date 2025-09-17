# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PurchaseReasonCancelWizard(models.TransientModel):
    _name = 'purchase.rma.reason.cancel.wizard'
    _description = 'Purchase Reason Cancel Wizard'

    claim_id = fields.Many2one('purchase.crm.claim.ept', string='Claim Id')
    reason_cancel = fields.Text(string="Reason Close", required=True)

    def action_confirm(self):
        self.claim_id.update({"reason_cancel": self.reason_cancel})
        self.claim_id.force_close()