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
    "name": "HDC Sale Quick Invoice",
    "category": "Sale",
    "version": "14.0.1.4",
    "summary": "Sale Can Open Quick Invoice",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["sale", "account", "stock", "hdc_inventory_picking_list_sale", "hdc_inter_transfer"],
    "data": [
        "data/ir_sequence.xml",
        "security/ir.model.access.csv",
        "views/stock_picking.xml",
        "views/urgent_delivery.xml",
        "views/urgent_delivery_line.xml",
        "views/generate_picking_list_view.xml",
        "views/stock_warehouse_views.xml",
        "wizard/wizard_add_urgent_delivery_view.xml",
        "wizard/wizard_remove_urgent_delivery_view.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
