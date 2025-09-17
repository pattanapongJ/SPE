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
    "name": "HDC Sale Orders Reports",
    "version": "14.0.2.0.2",
    "category": "",
    "summary": "Sale Orders Reports",
    "description": """
        Sale Orders Reports
    """,
    "author": "Hydra Data and Consulting Ltd",
    "website": "http://www.hydradataandconsulting.co.th",
    "depends": ["base", "sale","hdc_iso","hdc_billing_period_route"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/wizard_sale_report_view.xml",
        "data/report_paperformat_data.xml",
        'views/assets.xml',
        "views/sale_view.xml",
        "views/res_partner.xml",
        "views/res_company_view.xml",
        "reports/quotation_th_dis_report.xml",
        "reports/quotation_th_no_dis_report.xml",
        "reports/quotation_en_dis_report.xml",
        "reports/quotation_en_no_dis_report.xml",
        "reports/sale_order_th_dis_report.xml",
        "reports/sale_order_th_no_dis_report.xml",
        "reports/sale_order_en_dis_report.xml",
        "reports/sale_order_en_no_dis_report.xml",
        "reports/proforma_en_dis_report.xml",
        "reports/proforma_en_no_dis_report.xml",
        "reports/sale_order_report_views.xml",
        "reports/delivery_booth_en_report.xml",
        "reports/delivery_booth_qo_report.xml",
        "reports/delivery_booth_so_report.xml",
        "reports/sale_borrow_report.xml",
        "reports/quotation_d_th_dis_report.xml",
        "reports/quotation_d_th_no_dis_report.xml",
        "reports/sale_d_order_th_dis_report.xml",
        "reports/sale_d_order_th_no_dis_report.xml"
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
