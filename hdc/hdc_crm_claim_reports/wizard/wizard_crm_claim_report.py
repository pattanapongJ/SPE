from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardCrmClaimReport(models.TransientModel):
    _name = "wizard.crm.claim.report"
    _description = "wizard.crm.claim.report"

    document = fields.Selection([
        ("crm_claim", "ใบรับเรื่องร้องเรียนลูกค้า"),
    ],
    string="Documents"
    )

    crm_claim_id = fields.Many2one('crm.claim', string='Claim')
    state = fields.Char(string='State')
    
    def print(self):
        if self.document == "crm_claim":
            return self.env.ref('hdc_crm_claim_reports.crm_claim_template').report_action(self.crm_claim_id)