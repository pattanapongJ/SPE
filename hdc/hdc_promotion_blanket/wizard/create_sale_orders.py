# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class BlanketOrderWizard(models.TransientModel):
    _inherit = "sale.blanket.order.wizard"

    def _prepare_so_line_vals(self, line):
        vals = super()._prepare_so_line_vals(line)
        vals.update({
            "promotion_discount": line.blanket_line_id.promotion_discount,
            "is_reward_line": line.blanket_line_id.is_reward_line,
        })
        return vals
    
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
            "is_from_agreement": True,
        })
        return vals
        # return {
        #     "partner_id": customer,
        #     "origin": self.blanket_order_id.name,
        #     "user_id": user_id,
        #     "team_id": team_id,
        #     "sale_spec": sale_spec,
        #     "currency_id": currency_id,
        #     "pricelist_id": pricelist_id,
        #     "payment_term_id": payment_term_id,
        #     "order_line": order_lines_by_customer[customer],
        #     "analytic_account_id": self.blanket_order_id.analytic_account_id.id,
        #     "po_date": po_date,
        #     "expire_date":expire_date,
        #     "customer_contact_date":customer_contact_date,
        #     "client_order_ref":client_order_ref,
        #     "priority":priority,
        #     "warehouse_id":warehouse_id,
        #     "contact_person":contact_person,
        #     "validity_date":validity_date,
        #     "modify_type_txt":modify_type_txt,
        #     "type_id":type_id,
        #     "plan_home":plan_home,
        #     "fiscal_position_id":fiscal_position_id,
        #     "user_sale_agreement":user_sale_agreement,
        #     "sale_manager_id":sale_manager_id,
        #     "remark":remark,
        #     "requested_ship_date":requested_ship_date,
        #     "requested_receipt_date":requested_receipt_date,
        #     "delivery_trl":delivery_trl,
        #     "delivery_trl_description":delivery_trl_description,
        #     "delivery_company":delivery_company,
        #     "delivery_company_description":delivery_company_description,
        #     "days_delivery":days_delivery,
        #     "finance_dimension_1_id":finance_dimension_1_id,
        #     "finance_dimension_2_id":finance_dimension_2_id,
        #     "finance_dimension_3_id":finance_dimension_3_id,
        #     "global_discount":global_discount,
        #     "payment_method_id": self.blanket_order_id.payment_method_id.id,
        #     "billing_period_id": self.blanket_order_id.billing_period_id.id,
        #     "billing_route_id": self.blanket_order_id.billing_route_id.id,
        #     "billing_place_id": self.blanket_order_id.billing_place_id.id,
        #     "billing_terms_id": self.blanket_order_id.billing_terms_id.id,
        #     "payment_period_id": self.blanket_order_id.payment_period_id.id,
        #     "is_from_agreement": True,
        # }
    