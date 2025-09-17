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
    "name": "HDC RMA Dewalt",
    "category": "RMA",
    "description": """
        RMA Dewalt For Project SPE
    """,
    "version": "14.0.0.0.1",
    "development_status": "Mature",
    "summary": "RMA Dewalt",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "license": "AGPL-3",
    "depends": ["hdc_rma_modify_evaluation","hdc_add_from_no_header","hdc_sale_type_internal_transfer"],
    "data": [
        "security/ir.model.access.csv",
        "views/rma_dewalt_view.xml",
        "views/crm_claim_ept_view.xml",
        "views/repair_type_view.xml",
        "views/repair_order_view.xml",
        "views/sale_order_views.xml",
        "views/sale_order_type_view.xml",
        "views/stock_location_view.xml",
        "wizard/wizard_sale_report_view.xml",
        "data/report_paperformat_data.xml",
        "reports/dewalt_report_views.xml",
        "reports/delivery_dewalt_so_report.xml",
        "reports/claim_dewalt_so_report.xml",
        "reports/picking_list_report_dewalt_a5.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
