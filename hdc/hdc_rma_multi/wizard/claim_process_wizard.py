# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ClaimProcessWizard(models.TransientModel):
    _inherit = 'claim.process.wizard'

    def reject_claim(self):
        """reject claim with reason."""
        resault = super(ClaimProcessWizard, self).reject_claim()
        claim_line_ids = self.env['claim.line.ept'].search([
            ('id', 'in', self.env.context.get('claim_lines'))])
        claim = claim_line_ids[0].claim_id
        if claim.return_request_id:
            claim.return_request_id.re_compute_rma_qty()
        return resault
