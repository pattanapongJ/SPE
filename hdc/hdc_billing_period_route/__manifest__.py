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
    "name": "HDC Billing Period And Route",
    "version": "14.0.0.0.2",
    "category": "Account",
    "summary": "Add Billing Period And Billing Route",
    "description": """
        Add Billing Period And Billing Route
    """,
    "author": "Hydra Data and Consulting Ltd",
    "website": "http://www.hydradataandconsulting.co.th",
    "depends": ["hdc_add_from_no_header", "purchase_request", "purchase", "hdc_sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/account_billing_period_view.xml",
        "views/account_billing_route_view.xml",
        "views/partner_view.xml",
        "views/purchase_request_line_make_purchase_order_view.xml",
        "views/purchase_view.xml",
        "views/sale_views.xml",
        "views/account_move_views.xml",
        "views/credit_limit_view.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
