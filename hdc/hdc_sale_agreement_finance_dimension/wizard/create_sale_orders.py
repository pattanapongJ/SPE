# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class BlanketOrderWizard(models.TransientModel):
    _inherit = "sale.blanket.order.wizard"

    def _prepare_so_vals(
        self,
        customer,
        user_id,
        currency_id,
        pricelist_id,
        payment_term_id,
        order_lines_by_customer,
        
    ):
        vals = super()._prepare_so_vals(customer,user_id,currency_id,pricelist_id,payment_term_id,order_lines_by_customer)
        vals.update({
            "incoterm_id": self.blanket_order_id.incoterm_id.id,
            "finance_dimension_1_id":self.blanket_order_id.finance_dimension_1_id.id,
            "finance_dimension_2_id":self.blanket_order_id.finance_dimension_2_id.id,
            "finance_dimension_3_id":self.blanket_order_id.finance_dimension_3_id.id,
        })
        return vals
    
    # def _prepare_so_vals(
    #     self,
    #     customer,
    #     user_id,
    #     currency_id,
    #     pricelist_id,
    #     payment_term_id,
    #     order_lines_by_customer,
    #     team_id,
    #     sale_spec,
    #     expire_date,
    #     customer_contact_date,
    #     client_order_ref,
    #     priority,
    #     warehouse_id,
    #     contact_person,
    #     validity_date,
    #     modify_type_txt,
    #     type_id,
    #     plan_home,
    #     fiscal_position_id,
    #     user_sale_agreement,
    #     sale_manager_id,
    #     remark,
    #     requested_ship_date,
    #     requested_receipt_date,
    #     delivery_trl,
    #     delivery_trl_description,
    #     delivery_company,
    #     delivery_company_description, po_date,
    #     days_delivery,
    #     finance_dimension_1_id,
    #     finance_dimension_2_id,
    #     finance_dimension_3_id,
    #     global_discount,
    # ):
    #     return {
    #         "partner_id": customer,
    #         "origin": self.blanket_order_id.name,
    #         "user_id": user_id,
    #         "team_id": team_id,
    #         "sale_spec": sale_spec,
    #         "currency_id": currency_id,
    #         "pricelist_id": pricelist_id,
    #         "payment_term_id": payment_term_id,
    #         "order_line": order_lines_by_customer[customer],
    #         "analytic_account_id": self.blanket_order_id.analytic_account_id.id,
    #         "po_date": po_date,
    #         "expire_date":expire_date,
    #         "customer_contact_date":customer_contact_date,
    #         "client_order_ref":client_order_ref,
    #         "priority":priority,
    #         "warehouse_id":warehouse_id,
    #         "contact_person":contact_person,
    #         "validity_date":validity_date,
    #         "modify_type_txt":modify_type_txt,
    #         "type_id":type_id,
    #         "plan_home":plan_home,
    #         "fiscal_position_id":fiscal_position_id,
    #         "user_sale_agreement":user_sale_agreement,
    #         "sale_manager_id":sale_manager_id,
    #         "remark":remark,
    #         "requested_ship_date":requested_ship_date,
    #         "requested_receipt_date":requested_receipt_date,
    #         "delivery_trl":delivery_trl,
    #         "delivery_trl_description":delivery_trl_description,
    #         "delivery_company":delivery_company,
    #         "delivery_company_description":delivery_company_description,
    #         "days_delivery":days_delivery,
    #         "finance_dimension_1_id":finance_dimension_1_id,
    #         "finance_dimension_2_id":finance_dimension_2_id,
    #         "finance_dimension_3_id":finance_dimension_3_id,
    #         "global_discount":global_discount,
    #         "payment_method_id": self.blanket_order_id.payment_method_id.id,
    #         "billing_period_id": self.blanket_order_id.billing_period_id.id,
    #         "billing_route_id": self.blanket_order_id.billing_route_id.id,
    #         "billing_place_id": self.blanket_order_id.billing_place_id.id,
    #         "billing_terms_id": self.blanket_order_id.billing_terms_id.id,
    #         "payment_period_id": self.blanket_order_id.payment_period_id.id,
    #     }
    
    def _prepare_so_line_vals(self, line):
        return {
            "product_id": line.selected_product_id.id,
            "name": line.selected_product_id.name,
            "product_uom": line.product_uom.id,
            "sequence": line.blanket_line_id.sequence,
            "price_unit": line.blanket_line_id.price_unit,
            "blanket_order_line": line.blanket_line_id.id,
            "product_uom_qty": line.qty,
            "tax_id": [(6, 0, line.taxes_id.ids)],
            "analytic_tag_ids": [(6, 0, line.blanket_line_id.analytic_tag_ids.ids)],
            "sequence2":line.blanket_line_id.sequence2,
            "display_type":line.blanket_line_id.display_type,
            "pick_location_id":line.blanket_line_id.pick_location_id.id,
            "warehouse_id":line.blanket_line_id.warehouse_id.id,
            "finance_dimension_1_id":line.blanket_line_id.finance_dimension_1_id.id,
            "finance_dimension_2_id":line.blanket_line_id.finance_dimension_2_id.id,
            "discount":line.blanket_line_id.discount,
            "triple_discount":line.blanket_line_id.triple_discount,
            "rounding_price":line.blanket_line_id.rounding_price,
            "note":line.blanket_line_id.note,
            "barcode":line.blanket_line_id.barcode,
            "currency_id":line.blanket_line_id.currency_id.id,
            "company_id":line.blanket_line_id.company_id.id,
            "is_global_discount":line.blanket_line_id.is_global_discount,
        }

    # def create_sale_order(self):
    #     order_lines_by_customer = defaultdict(list)
    #     currency_id = 0
    #     pricelist_id = 0
    #     user_id = 0
    #     payment_term_id = 0
    #     team_id = self.blanket_order_id.team_id.id
    #     sale_spec = self.blanket_order_id.sale_spec.id
    #     expire_date = self.blanket_order_id.expire_date
    #     customer_contact_date = self.blanket_order_id.customer_contact_date
    #     client_order_ref = self.blanket_order_id.client_order_ref
    #     priority = self.blanket_order_id.priority
    #     warehouse_id = self.blanket_order_id.warehouse_id.id
    #     contact_person = self.blanket_order_id.contact_person.id
    #     validity_date = self.blanket_order_id.validity_date
    #     modify_type_txt = self.blanket_order_id.modify_type_txt
    #     type_id = self.blanket_order_id.sale_type_id.id
    #     plan_home = self.blanket_order_id.plan_home
    #     fiscal_position_id = self.blanket_order_id.fiscal_position_id.id
    #     user_sale_agreement = self.blanket_order_id.administrator.id
    #     sale_manager_id = self.blanket_order_id.sale_manager_id.id
    #     remark = self.blanket_order_id.remark
    #     requested_ship_date = self.blanket_order_id.requested_ship_date
    #     requested_receipt_date = self.blanket_order_id.requested_receipt_date
    #     delivery_trl = self.blanket_order_id.delivery_trl.id
    #     delivery_trl_description = self.blanket_order_id.delivery_trl_description
    #     delivery_company = self.blanket_order_id.delivery_company.id
    #     delivery_company_description = self.blanket_order_id.delivery_company_description
    #     po_date = self.blanket_order_id.po_date
    #     days_delivery = self.blanket_order_id.days_delivery
    #     global_discount = self.blanket_order_id.global_discount
    #     finance_dimension_1_id = self.blanket_order_id.finance_dimension_1_id.id
    #     finance_dimension_2_id = self.blanket_order_id.finance_dimension_2_id.id
    #     finance_dimension_3_id = self.blanket_order_id.finance_dimension_3_id.id

    #     for line in self.line_ids.filtered(lambda l: l.qty != 0.0):
    #         if line.qty > line.remaining_uom_qty:
    #             raise UserError(_("You can't order more than the remaining quantities"))
    #         vals = self._prepare_so_line_vals(line)
    #         order_lines_by_customer[line.partner_id.id].append((0, 0, vals))

    #         if currency_id == 0:
    #             currency_id = line.blanket_line_id.order_id.currency_id.id
    #         elif currency_id != line.blanket_line_id.order_id.currency_id.id:
    #             currency_id = False

    #         if pricelist_id == 0:
    #             pricelist_id = line.blanket_line_id.pricelist_id.id
    #         elif pricelist_id != line.blanket_line_id.pricelist_id.id:
    #             pricelist_id = False

    #         if user_id == 0:
    #             user_id = line.blanket_line_id.user_id.id
    #         elif user_id != line.blanket_line_id.user_id.id:
    #             user_id = False

    #         if payment_term_id == 0:
    #             payment_term_id = line.blanket_line_id.payment_term_id.id
    #         elif payment_term_id != line.blanket_line_id.payment_term_id.id:
    #             payment_term_id = False

    #     if not order_lines_by_customer:
    #         raise UserError(_("An order can't be empty"))

    #     if not currency_id:
    #         raise UserError(
    #             _(
    #                 "Can not create Sale Order from Blanket "
    #                 "Order lines with different currencies"
    #             )
    #         )
        
    #     res = []
    #     for customer in order_lines_by_customer:
    #         order_vals = self._prepare_so_vals(
    #             customer,
    #             user_id,
    #             currency_id,
    #             pricelist_id,
    #             payment_term_id,
    #             order_lines_by_customer,
    #             team_id,
    #             sale_spec,
    #             expire_date,
    #             customer_contact_date,
    #             client_order_ref,
    #             priority,
    #             warehouse_id,
    #             contact_person,
    #             validity_date,
    #             modify_type_txt,
    #             type_id,
    #             plan_home,
    #             fiscal_position_id,
    #             user_sale_agreement,
    #             sale_manager_id,
    #             remark,
    #             requested_ship_date,
    #             requested_receipt_date,
    #             delivery_trl,
    #             delivery_trl_description,
    #             delivery_company,
    #             delivery_company_description, po_date,
    #             days_delivery,
    #             finance_dimension_1_id,
    #             finance_dimension_2_id,
    #             finance_dimension_3_id,
    #             global_discount,
    #         )
    #         sale_order = self.env["sale.order"].create(order_vals)
    #         res.append(sale_order.id)
            
    #     return {
    #         "domain": [("id", "in", res)],
    #         "name": _("Sales Orders"),
    #         "view_type": "form",
    #         "view_mode": "tree,form",
    #         "res_model": "sale.order",
    #         "context": {"from_sale_order": True},
    #         "type": "ir.actions.act_window",
    #     }


