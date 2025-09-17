from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

    
class PickingType(models.Model):
    _inherit = "stock.picking.type"

    is_rg = fields.Boolean(string='Is RG')


