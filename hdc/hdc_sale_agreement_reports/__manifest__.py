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
    "name": "HDC Sale Agreement Reports",
    "category": "Sale",
    "version": "14.0.0.0.2",
    "summary": "Addon HDC Sale Agreement Reports",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["hdc_sale_agreement_addon","hdc_discount"],
    "data": [
        "data/report_paperformat_data.xml",
        "security/ir.model.access.csv",
        "views/sale_blanket_order_views.xml",
        "reports/blanket_orders_th_dis_report.xml",
        "reports/blanket_orders_th_no_dis_report.xml",
        "reports/blanket_orders_en_dis_report.xml",
        "reports/blanket_orders_en_no_dis_report.xml",
        "reports/blanket_orders_proforma_en_dis_report.xml",
        "reports/blanket_orders_proforma_en_no_dis_report.xml",
        "reports/delivery_item_report.xml",
        "reports/blanket_orders_report_views.xml",
        "wizard/wizard_blanket_orders_report_view.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
