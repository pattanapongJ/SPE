from odoo import models, fields

class AccountAsset(models.Model):
    _inherit = 'account.asset'

    asset_location_id = fields.Many2one(
        'account.asset.location', 
        string="Asset Location"
    )
    
    asset_responsible_id = fields.Many2one(
        'res.partner',
        string="Asset Responsible", 
        help="Employee responsible for this asset.",
        store=True
    )
