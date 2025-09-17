from odoo import _, api, fields, models

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"