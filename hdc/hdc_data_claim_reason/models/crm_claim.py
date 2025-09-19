from odoo import api, fields, models


class CrmClaim(models.Model):
    _inherit = "crm.claim"

    claim_reason = fields.Many2one(
        "data.claim.reason",
        string="Claim Reason"
    )

    receive_claim = fields.Boolean(
        string="Receive Claim",
        default=False,
        help="Check this box if the claim is received."
    )

    reject_claim = fields.Boolean(
        string="Reject Claim",
        default=False,
        help="Check this box if the claim is rejected."
    )