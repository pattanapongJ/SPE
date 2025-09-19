# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _inherit = "purchase.request.line.make.purchase.order"

    billing_period_id = fields.Many2one(comodel_name='account.billing.period', string="Billing Period")

    billing_route_id = fields.Many2one(comodel_name='account.billing.route', string="Billing Route")

    @api.onchange('supplier_id')
    def _onchange_supplier_id(self):

        if self.supplier_id.billing_period_id:
            self.billing_period_id = self.supplier_id.billing_period_id
        
        if self.supplier_id.billing_route_id:
            self.billing_route_id = self.supplier_id.billing_route_id

    @api.model
    def _prepare_purchase_order(self, picking_type, group_id, company, origin):
        res = super(PurchaseRequestLineMakePurchaseOrder, self)._prepare_purchase_order(picking_type, group_id, company, origin)

        if self.billing_period_id.id or self.billing_route_id.id:
            res['billing_period_id'] = self.billing_period_id.id
            res['billing_route_id'] = self.billing_route_id.id

        return res

    # def make_purchase_order(self):
    #     res = []
    #     purchase_obj = self.env["purchase.order"]
    #     po_line_obj = self.env["purchase.order.line"]
    #     pr_line_obj = self.env["purchase.request.line"]
    #     purchase = False

    #     for item in self.item_ids:
    #         line = item.line_id
    #         if item.product_qty <= 0.0:
    #             raise UserError(_("Enter a positive quantity."))
    #         if self.purchase_order_id:
    #             purchase = self.purchase_order_id
    #         if not purchase:
    #             po_data = self._prepare_purchase_order(
    #                 line.request_id.picking_type_id,
    #                 line.request_id.group_id,
    #                 line.company_id,
    #                 line.origin,
    #             )
    #             purchase = purchase_obj.create(po_data)

    #         # Look for any other PO line in the selected PO with same
    #         # product and UoM to sum quantities instead of creating a new
    #         # po line
    #         domain = self._get_order_line_search_domain(purchase, item)
    #         available_po_lines = po_line_obj.search(domain)
    #         new_pr_line = True
    #         # If Unit of Measure is not set, update from wizard.
    #         if not line.product_uom_id:
    #             line.product_uom_id = item.product_uom_id
    #         # Allocation UoM has to be the same as PR line UoM
    #         alloc_uom = line.product_uom_id
    #         wizard_uom = item.product_uom_id
    #         if available_po_lines and not item.keep_description:
    #             new_pr_line = False
    #             po_line = available_po_lines[0]
    #             po_line.purchase_request_lines = [(4, line.id)]
    #             po_line.move_dest_ids |= line.move_dest_ids
    #             po_line_product_uom_qty = po_line.product_uom._compute_quantity(
    #                 po_line.product_uom_qty, alloc_uom
    #             )
    #             wizard_product_uom_qty = wizard_uom._compute_quantity(
    #                 item.product_qty, alloc_uom
    #             )
    #             all_qty = min(po_line_product_uom_qty, wizard_product_uom_qty)
    #             self.create_allocation(po_line, line, all_qty, alloc_uom)
    #         else:
    #             po_line_data = self._prepare_purchase_order_line(purchase, item)
    #             if item.keep_description:
    #                 po_line_data["name"] = item.name
    #             po_line = po_line_obj.create(po_line_data)
    #             po_line_product_uom_qty = po_line.product_uom._compute_quantity(
    #                 po_line.product_uom_qty, alloc_uom
    #             )
    #             wizard_product_uom_qty = wizard_uom._compute_quantity(
    #                 item.product_qty, alloc_uom
    #             )
    #             all_qty = min(po_line_product_uom_qty, wizard_product_uom_qty)
    #             self.create_allocation(po_line, line, all_qty, alloc_uom)
    #         # TODO: Check propagate_uom compatibility:
    #         new_qty = pr_line_obj._calc_new_qty(
    #             line, po_line=po_line, new_pr_line=new_pr_line
    #         )
    #         po_line.product_qty = new_qty
    #         po_line._onchange_quantity()
    #         # The onchange quantity is altering the scheduled date of the PO
    #         # lines. We do not want that:
    #         date_required = item.line_id.date_required
    #         po_line.date_planned = datetime(
    #             date_required.year, date_required.month, date_required.day
    #         )
    #         res.append(purchase.id)


        
