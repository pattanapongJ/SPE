from odoo import models, fields, tools, api, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError

class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    transfer_lines = fields.One2many("hdc.transfer.line", "picking_id", "Transfer Lines")

