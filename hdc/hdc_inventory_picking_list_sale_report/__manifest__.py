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
    'name': 'HDC Inventory Picking List by order Report',
    'version': '14.0.3',
    'category': 'Sale',
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    'description': """
        Create Picking from order line sale
    """,
    'depends': ['hdc_inventory_picking_list_sale','web',],
    'data': [
        'security/ir.model.access.csv',
        'data/report_paperformat_data.xml',
        'views/generate_picking_list_view.xml',
        # 'views/generate_picking_list_report.xml',
        'views/layouts.xml',
        'wizard/wizard_picking_list_report_view.xml',
        'reports/picking_list_report_th_history.xml',
        'reports/picking_list_report_th_history_1.xml',
        'reports/picking_list_report_th_history_portrait.xml',
        'reports/picking_list_report_th_history_portrait_multi.xml',
        'reports/picking_list_report_th_history_a5.xml',
        'reports/picking_list_report_th_history_a5_multi.xml',
        'reports/picking_list_report_views.xml',
        'reports/picking_list_report_th_history_portrait_booth.xml',
        'reports/picking_list_report_th_history_portrait_road_show.xml',
        'reports/picking_list_report_th_history_portrait_sale_consignment.xml',
        'reports/picking_list_report_th_history_portrait_consignment.xml',
        'reports/generate_picking_lists_report.xml',
        'wizard/wizard_generate_picking_list_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
###################################################################################
