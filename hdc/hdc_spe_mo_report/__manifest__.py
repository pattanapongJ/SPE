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
    "name": "HDC SPE MO Reports",
    "version": "14.0.0.0.3",
    "category": "MRP Reports",
    "summary": "SPE MO Reports",
    "description": """
        SPE MO Reports
    """,
    "author": "Hydra Data and Consulting Ltd",
    "website": "http://www.hydradataandconsulting.co.th",
    "depends": ["base", 'mrp', 'product', 'stock', 'resource','hdc_mrp_machines','hdc_mrp_general_report','hdc_mrp_mr'],
    "data": [
        "security/ir.model.access.csv",
        'data/report_paperformat_data.xml',
        "reports/mrp_production_report.xml",
        "reports/requestion_inventory_report.xml",
        "reports/requestion_cutting_inventory_report.xml",
        "reports/mrp_production_state_report.xml",
        "reports/mrp_fg_ls_report.xml",
        
        "views/material_requisition_type_view.xml",
        "views/mrp_production_views.xml",
        "views/mrp_routing_views.xml",
        "views/mrp_production_state_view.xml",
        "views/mrp_bom_views.xml",
        "views/iso_operation_type_views.xml",
        "wizard/wizard_mrp_report_view.xml",
        "wizard/wizard_mrp_cutting_report_view.xml",

    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
