# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ReasonCancelWizard(models.TransientModel):
    _name = 'rma.reason.cancel.wizard'
    _description = 'Reason Cancel Wizard'

    claim_id = fields.Many2one('crm.claim.ept', string='Claim Id')
    reason_cancel = fields.Text(string="Reason Cancel", required=True)

    def action_confirm(self):
        self.claim_id.update({"reason_cancel": self.reason_cancel})
        self.claim_id.force_close()