from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order"

    purchase_order_type = fields.Many2one(
        comodel_name="purchase.order.type",
        string="Purchase Order Type",
        required=True 
    )

    @api.onchange("supplier_id")
    def onchange_supplier_id(self):
        purchase_type = (
                self.supplier_id.purchase_type
                or self.supplier_id.commercial_partner_id.purchase_type
        )
        if purchase_type:
            self.purchase_order_type = purchase_type

    @api.model
    def _prepare_purchase_order(self, picking_type, group_id, company, origin):
        data = super()._prepare_purchase_order(picking_type,group_id,company,origin)
        data.update({
            'order_type':self.purchase_order_type.id,
            'customer': self.item_ids.request_id.for_customer.name
        })
        return data    

    def make_purchase_order(self):
        result = super().make_purchase_order()

        domain = result.get("domain",False)
        if domain:
            res_ids = domain[0][2]
            purchase_list = self.env['purchase.order'].sudo().browse(res_ids)
            if purchase_list.exists():
                purchase_list.onchange_order_type()
        return result
    
    
    
        





