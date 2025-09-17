# Copyright 2023 Basic Solution Co.,Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

class PurchaseRequest(models.Model):
    
    _inherit = "purchase.request"
    _description = "Purchase Request"

    request_date = fields.Date(string="Request Date", store=True)
    expire_date = fields.Date(string="Expire Date", store=True)
    