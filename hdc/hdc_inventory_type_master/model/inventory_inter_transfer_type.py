from odoo import api, fields, models
from odoo.exceptions import UserError

class InventoryInterTransferType(models.Model):
    _name = 'inventory.inter.transfer.type'
    _description = 'Inventory Inter Transfer Type'

    name = fields.Char(string='Inter Transfer Type', required=True)
    description = fields.Char(string='Description')