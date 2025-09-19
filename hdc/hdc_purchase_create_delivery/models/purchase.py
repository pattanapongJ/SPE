# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_stock_moves(self, picking):
        move_vals = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        for move in move_vals:
            if self.order_id.partner_id:
                move['partner_id'] = self.order_id.partner_id.id
        return move_vals
