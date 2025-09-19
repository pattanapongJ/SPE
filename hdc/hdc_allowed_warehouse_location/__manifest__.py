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
    'name': 'HDC Allowed Warehouse And Location',
    'version': '14.0.1',
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    'description': """
        HDC Allowed Warehouse And Location
    """,
    'depends': ['base', 'stock'],
    'data': [
        'views/res_users.xml',
        'views/stock_location_views.xml',
        'views/stock_picking_views.xml',
        # 'views/stock_quant_views.xml',
        'views/stock_orderpoint_views.xml',
        'views/stock_template.xml',
        'views/stock_warehouse_views.xml',

    ],
    'qweb': [
        'static/src/xml/report_stock_forecasted.xml',
    ],
    'post_init_hook': '_post_init_hook',

    'installable': True,
    'auto_install': False,
    'application': True,
}
###################################################################################
