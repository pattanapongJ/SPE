# Copyright 2023 Basic Solution Co.,Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

class PurchaseRequest(models.Model):
    
    _inherit = "purchase.order.line"
    _description = "Purchase Order Line"

    finished_qty = fields.Float(string='Finished Qty.', digits='Product Unit of Measure', index=True, store=True)
    finished_note = fields.Char('Finished Notes', index=True, store=True)

    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        name = "-"
        if product_lang.description_purchase:
            name = product_lang.description_purchase
        return name
    


class PurchaseOrder(models.Model):
    
    _inherit = "purchase.order"
    _description = "purchase.order"
    
    carrier_id = fields.Many2one("delivery.carrier", string="Shipping Method")
    