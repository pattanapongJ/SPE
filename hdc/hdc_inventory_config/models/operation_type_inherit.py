from tokenize import String
from odoo import fields, models, api

class Inventory_inherit(models.Model):
    _inherit = "stock.picking.type"

    addition_operation_types = fields.Many2one('addition.operation.type', String="Addition Operation Type")
    is_internal_transfer = fields.Boolean(string='Is Internal Transfer')