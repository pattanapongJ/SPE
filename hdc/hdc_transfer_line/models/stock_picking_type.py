from odoo import models, fields, tools, api, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError

class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    is_internal_transfer = fields.Boolean("Internal Transfer")

