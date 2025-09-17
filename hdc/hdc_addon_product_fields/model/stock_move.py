from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class StockMove(models.Model):
    _inherit = "stock.move"

    tags_product_sale_ids = fields.Many2many(related='product_id.tags_product_sale_ids', string='Tags')
