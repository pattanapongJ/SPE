# -*- coding: utf-8 -*-
###################################################################################
#    Hydra Data and Consulting Ltd.
#    Copyright (C) 2019 Hydra Data and Consulting Ltd. (<http://www.hydradataandconsulting.co.th>).
#    Author: Hydra Data and Consulting Ltd. (<http://www.hydradataandconsulting.co.th>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

{
    "name": "HDC User Employee",
    "version": "14.0.0.0.1",
    "category": "Human Resources/Employees",
    "description": """
        HDC User Employee.
    """,
    "author": "Hydra Data and Consulting Ltd",
    "website": "http://www.hydradataandconsulting.co.th",
    "depends": ["hdc_sale_team_addon",
                "hr",
                "hdc_pricelist_shipping_cost",
                "hdc_creditlimit_saleteam",
                "hdc_sale_targets",
                "hdc_extra_field_stock_picking",
                "hdc_mrp_multi_scrap",
                "hdc_rma_multi",
                "hdc_inventory_borrow",
                "hdc_inventory_adj_confirm",
                "rma_ept",
                "hdc_rma_ept_purchase"],
    "data": [
        "security/ir.model.access.csv",
        "views/sales_team_views.xml",
        "views/sale_view.xml",
        "views/quotation_view.xml",
        "views/blanket_orders_view.xml",
        "views/account_move_view.xml",
        "views/hr_employee_view.xml",
        "views/credit_limit_view.xml",
        "views/employee_sale_team_history_view.xml",
        "views/res_users.xml",
        "views/res_partner_view.xml",
        "views/sale_targets_view.xml",
        "views/credit_limit_request.xml",
        "views/customer_return_request_view.xml",
        "views/stock_picking_view.xml",
        "views/multi_scrap_views.xml",
        "views/stock_inventory.xml",
        "views/crm_claim_ept_view.xml",
        "views/repair_views.xml",
        "views/mrp_mr_views.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": False,
}
