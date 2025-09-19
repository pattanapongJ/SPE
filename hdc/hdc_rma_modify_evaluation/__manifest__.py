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
    "name": "HDC SPE RMA Modify Evaluation",
    "category": "RMA",
    "description": """
        SPE RMA Modify Evaluation
    """,
    "version": "14.0.0.0.5",
    "development_status": "Mature",
    "summary": "Addon HDC CRM Hydra",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "license": "AGPL-3",
    "depends": ["rma_ept","base","repair_sale_order",
                "hdc_sale","mrp","hdc_sale_type",
                "hdc_inter_company_transactions","hdc_inter_transfer",
                "hdc_mrp_mr","hdc_inventory_config","hdc_billing_period_route",
                "hdc_fiscal_position_by_company"],
    "data": [
        "security/ir.model.access.csv",
        "views/crm_claim_ept_view.xml",
        "views/repair_order_view.xml",
        "views/sale_order_type_view.xml",
        "views/sale_order_views.xml",
        "views/stock_picking_view.xml",
        "views/request_tyre_mr_views.xml",
        "views/product_view.xml",
        "views/mrp_mr_views.xml",
        "wizard/view_claim_process_wizard.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
