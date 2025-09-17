# Copyright 2024 Basic Solution Co.,Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

class PurchaseOrder(models.Model):
    
    _inherit = "purchase.order"
    _description = "purchase.order"
    
    carrier_id_spe = fields.Many2one("delivery.carrier", string="Delivery Mode")
    