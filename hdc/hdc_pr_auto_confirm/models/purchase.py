# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for purchase in self:
            pr = purchase.mapped("order_line.purchase_request_lines.request_id")
            check = True
            if pr:
                for line in pr.line_ids:
                    if line.product_qty - line.purchased_qty > 0:
                        check = False
                
            if check:
                pr.button_done()          

            return res