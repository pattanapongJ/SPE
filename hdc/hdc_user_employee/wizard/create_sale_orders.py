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
            "user_employee_id": self.blanket_order_id.user_employee_id.id,
            "sale_spec_employee":self.blanket_order_id.sale_spec_employee.id,
            "sale_manager_employee_id":self.blanket_order_id.sale_manager_employee_id.id,
            "user_sale_agreement_employee":self.blanket_order_id.administrator_employee.id,
            "department_id": self.blanket_order_id.department_id.id,
        })
        return vals