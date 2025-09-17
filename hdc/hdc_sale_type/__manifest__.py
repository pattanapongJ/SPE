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
    "name": "HDC Sale Type Hydra",
    "version": "14.0.1.0.1",
    "category": "Hydra Warehouse",
    "description": """
        HDC Sale Type Hydra.
    """,
    "author": "Hydra Data and Consulting Ltd",
    "website": "http://www.hydradataandconsulting.co.th",
    "depends": ["base", "sale", "sale_order_type", "sales_team", "sale_blanket_order","stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_type_view.xml",
        "views/sales_team_views.xml",
        "views/sale_blanket_order_views.xml",
        "views/sale_views.xml",
        "views/stock_picking_views.xml",
        "wizard/agreement_below_cost_wizard.xml"
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": False,
}
