from odoo import api, fields, models


class DataClaimReason(models.Model):
    _name = "data.claim.reason"

    claim_reason = fields.Char(string="Claim Reason")

    def name_get(self):
        result = []
        for record in self:
            rec_name = record.claim_reason
            result.append((record.id, rec_name))
        return result