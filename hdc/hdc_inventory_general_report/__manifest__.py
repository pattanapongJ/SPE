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
    'name': 'HDC Inventory General Report',
    'version': '14.0.2',
    'category': 'stock',
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    'description': """
        HDC Inventory General Report
    """,
    'depends': ['base', 'stock', 'hdc_inter_transfer', 'hdc_inter_transfer_addon_field'],
    'data': [
        'security/ir.model.access.csv',
        'data/report_paperformat_data.xml',
        'reports/receipt_inventory_report.xml',
        'reports/receipt_inventory_report_en.xml',
        'reports/receipt_shortage_overage_report.xml',
        'reports/internal_tranfer_inventory_report.xml',
        'reports/delivery_inventory_report.xml',
        'reports/inter_tranfer_inventory_report.xml',
        'reports/requestion_inventory_report.xml',
        'reports/requestion_inventory_ls_report.xml',
        'reports/return_cus_inventory_report.xml',
        'reports/inventory_report_views.xml',
        'reports/tranfers_inventory_ls_report.xml',
        'reports/tranfers_inventory_llk_report.xml',
        'reports/batch_inventory_report.xml',
        'reports/picking_list_report_th_history_portrait.xml',
        'reports/picking_list_report_th_history_a5.xml',
        'reports/hdc_inv_adj_report.xml',
        'reports/invoice_borrow_report.xml',
        'reports/inventory_borrow_a4_report.xml',
        'wizard/wizard_borrow_view.xml',
        'wizard/wizard_receipt_view.xml',
        'wizard/wizard_inter_tranfers_view.xml',
        'wizard/wizard_inventory_picking_list_report_view.xml',
        'views/assets.xml',
        'views/stock_picking_batch_views.xml',
        'views/stock_picking_views.xml'
        # 'views/res_config_settings_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
###################################################################################
