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
    "name": "HDC Extra Field Stock Picking",
    "version": "14.0.0.0.0",
    "category": "Inventory",
    "summary": "Add Field in Stock Picking Form",
    "description": """
        Add Field in Stock Picking Form
    """,
    "author": "Hydra Data and Consulting Ltd",
    "website": "http://www.hydradataandconsulting.co.th",
    "depends": [
        "sale",
        "stock",
        "hdc_inventory_borrow",
        "hdc_inventory_borrow_sale",
        "branch",
        "hdc_inter_transfer_addon_field",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/inventory_borrow_inherit.xml",
        "views/inherited_stock_picking.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
