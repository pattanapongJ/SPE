
from odoo import _, api, fields, models
from odoo.exceptions import UserError

class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'
    