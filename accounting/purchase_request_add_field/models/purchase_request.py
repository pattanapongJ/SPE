# Copyright 2023 Basic Solution Co.,Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

class PurchaseRequest(models.Model):
    _inherit = "purchase.request"
    _description = "Purchase Request"

    currency_id = fields.Many2one('res.currency',string="Curency", store=True)
    
    
    
    
class PurchaseRequestLine(models.Model):
    _inherit = "purchase.request.line"
    _description = "Purchase Request Line"
    
    purchase_request_line_note = fields.Char(string="Note")