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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
###################################################################################

{
    "name": "HDC Receipt List",
    "category": "stock",
    "version": "14.0.1.1.1",
    "summary": "Create Receipt List",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["base", "account", "stock", "purchase", "purchase_order_type", "hdc_addon_product_fields","hdc_inter_transfer","hdc_confirm_warehouse","hdc_vendor"],
    "data": [
        "data/data_sequence.xml",
        "data/report_paperformat_data.xml",
        "data/ir_cron_data.xml",
        "security/ir.model.access.csv",
        "wizard/cancel_receipt_list_wizard_view.xml",
        "wizard/confirm_receipt_list_wizard.xml",
        "wizard/wizard_split_receipt_in_view.xml",
        "wizard/purchases_make_invoice_advance_views.xml",
        "reports/receipt_list_report_views.xml",
        "reports/receipt_shortage_overage_report.xml",
        "reports/receipt_list_report.xml",
        "views/receipt_list_view.xml",
        "views/gen_receipt_list_view.xml",
        "views/gen_billing.xml",
        "views/purchase_view.xml",
        "views/stock_move.xml",
        'views/account_move.xml',
        "views/stock_picking_view.xml",
        "views/menu_view.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
