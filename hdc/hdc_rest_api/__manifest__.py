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
    'name': 'HDC Rest API Hydra',
    'version': '14.0.1.0.0',
    'category': 'Rest API Hydra',
    "summary" : "Rest API",
    'description': """
        Sale Order
    """,
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    'depends': ['base','hdc_addon_branch_api','sale_stock', 'hdc_multi_scrap', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'data/product_data.xml',
        'views/res_config_settings_views.xml',
        'views/stock_view.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
