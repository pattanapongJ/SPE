# Copyright 2022 Basic Solution Co.,Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

class AccountAsset(models.Model):
    
    _inherit = "account.asset"
    _description = "Asset"

    asset_code = fields.Char(string="Asset Code", store=True)