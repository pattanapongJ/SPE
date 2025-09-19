from odoo import api, fields, models
from odoo.osv import expression

class AccountAssetLocation(models.Model):
    _name = "account.asset.location"
    _description = "Asset Location"
    _order = "code, name"

    name = fields.Char(string="Name", size=64, required=True, index=True)
    code = fields.Char(index=True)
    