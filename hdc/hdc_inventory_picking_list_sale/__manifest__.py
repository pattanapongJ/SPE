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
{
    'name': 'HDC Inventory Picking List by order',
    'version': '14.0.8',
    'category': 'Sale',
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    'description': """
        Create Picking from order line sale
    """,
    'depends': ['sale', 'stock', 'sale_stock','hdc_sale_project','is_customer_is_vendor'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/sale_views.xml',
        'views/generate_picking_list_view.xml',
        'views/stock_move.xml',
        'views/account_move_view.xml',
        'wizard/wizard_create_picking_list.xml',
        'wizard/wizard_confirm_create_picking_list.xml',
        'wizard/wizard_picking_list_backorder.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
###################################################################################
