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
    "name": "HDC Sale Type Internal Transfer",
    "version": "14.0.0.0.3",
    "category": "Sale",
    "summary": "Make filter Sale Type Internal Transfer",
    "description": """
        Make filter Sale Type Internal Transfer
    """,
    "author": "Hydra Data and Consulting Ltd",
    "website": "http://www.hydradataandconsulting.co.th",
    "depends": ["hdc_sale_type","stock"
                ,"hdc_inter_company_transactions"
                ,"hdc_inter_transfer_addon_field"
                ,"hdc_confirm_warehouse"
                ,"hdc_sale_agreement_addon"
                ,"hdc_quotation_order"
                ,"hdc_inventory_picking_list_sale"
                ,"hdc_mrp_mr_sale"
                ,"hdc_sale_quick_invoice"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "views/sale_order_type_view.xml",
        "views/sale_order_views.xml",
        "views/stock_location_view.xml",
        "views/sale_blanket_order_views.xml",
        "views/booth_consign_urgent_delivery_view.xml",
        "views/stock_picking.xml",
        "wizard/wizard_error_no_stock_view.xml",
        "wizard/below_cost_warning_wizard_booth.xml",
        "wizard/wizard_add_booth_consign_urgent_delivery_view.xml",
        "wizard/wizard_remove_booth._consign_urgent_delivery_view.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
