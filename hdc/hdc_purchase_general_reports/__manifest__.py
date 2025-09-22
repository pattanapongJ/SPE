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
    "name": "HDC Purchase Orders Reports",
    "version": "14.0.2.0.7",
    "category": "Purchase Orders Reports",
    "summary": "Purchase Orders Reports",
    "description": """
        Purchase Orders Reports
    """,
    "author": "Hydra Data and Consulting Ltd",
    "website": "http://www.hydradataandconsulting.co.th",
    "depends": ["base", "purchase","purchase_request","stock",'hdc_iso','hdc_branch_addon_fields'],
    "data": [
        "security/ir.model.access.csv",
        "wizard/wizard_purchase_report_view.xml",
        "data/report_paperformat_data.xml",
        'views/assets.xml',
        "views/purchase_view.xml",
        "views/res_partner.xml",
        "views/res_company_view.xml",
        "views/product_views.xml",
        "reports/purchase_order_rfq_report_th.xml",
        "reports/purchase_order_rfq_report_en.xml",
        "reports/purchase_order_report_th.xml",
        "reports/purchase_order_report_en.xml",
        "reports/purchase_report_views.xml",
        "reports/purchase_request_report.xml",
        "reports/purchase_order_report_th_history.xml",
        "reports/purchase_order_report_th_internal.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
