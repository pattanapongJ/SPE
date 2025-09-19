from odoo import fields, models

class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    request_type = fields.Many2one(comodel_name="purchase.request.type",string="PR Type",)
