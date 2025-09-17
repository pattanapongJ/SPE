from odoo import models

class AccountAsset(models.Model):
    _inherit = 'account.asset'
    
    # Override
    def validate(self):
        for asset in self:
            asset_profile = asset.profile_id
            if (
                asset.number in [False, ""]
                and asset_profile.use_sequence
                and asset_profile.sequence_id
            ):
                seq_date = asset.date_start
                asset.number = asset_profile.sequence_id.with_context(ir_sequence_date=seq_date).next_by_id()
        return super().validate()