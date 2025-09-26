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
    "name": "HDC Inventory Borrow Sale",
    "summary": "Inventory Borrow",
    "version": "14.0.1.0.2",
    "category": "Warehouse",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "license": "AGPL-3",
    "depends": ["sale","hdc_inventory_borrow","sale_order_type"],
    "data": [   
                "security/ir.model.access.csv",
                "views/sale_view.xml",
                "views/stock_picking.xml",
                "wizard/wizard_borrow_force_done_view.xml",
                "views/inherit_is_borrow.xml"
            ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
