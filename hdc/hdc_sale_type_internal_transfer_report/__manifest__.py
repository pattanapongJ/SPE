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
    'name': 'HDC Sale Type Internal Transfer Report',
    'version': '14.0.3',
    'category': 'Inventory',
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    'description': """
        Sale Type Internal Transfer Report
    """,
    'depends': ['hdc_sale_type_internal_transfer','hdc_inventory_general_report','web',],
    'data': [
        'security/ir.model.access.csv',
        'data/report_paperformat_data.xml',
        'wizard/wizard_sale_type_report_view.xml',
        'wizard/wizard_sale_type_return_booth_report_view.xml',
        'reports/sale_type_internal_transfer_report_views.xml',
        'reports/sale_type_internal_transfer_report_booth.xml',
        'reports/sale_type_internal_transfer_report_road_show.xml',
        'reports/sale_type_internal_transfer_report_sale_consignment.xml',
        'reports/sale_type_internal_transfer_report_consignment.xml',
        'reports/sale_type_internal_transfer_report_consignment_return.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
###################################################################################
