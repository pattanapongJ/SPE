from odoo import fields, models

class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    is_internal_borrow = fields.Boolean(string="Internal Borrow",store=True)
    is_internal_return = fields.Boolean(string="Internal Return",store=True)
