# Copyright 2023 Basic Solution Co.,Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

class PurchaseRequest(models.Model):
    _inherit = "purchase.request"
    
    is_create_pr = fields.Boolean(
        string="Is Create PR",
        default=False,
    )
        
class PurchaseRequestsLine(models.Model):
    _inherit = 'purchase.request.line'
