from odoo import api, fields, models
from odoo.exceptions import UserError

class InventoryBorrowferType(models.Model):
    _name = 'inventory.borrow.type'
    _description = 'Inventory Borrow Type'

    name = fields.Char(string='Borrow Type', required=True)
    description = fields.Char(string='Description')
    type_borrow = fields.Selection(
        selection=[
            ("borrow", "เบิกยืมคืน"),
            ("borrow_use", "เบิกไปใช้")
        ],
        string="Type",
        # default="borrow"
    )