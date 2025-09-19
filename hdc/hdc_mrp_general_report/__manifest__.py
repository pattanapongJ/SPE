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
    "name": "HDC MRP Orders Reports",
    "version": "14.0.2.0.0",
    "category": "MRP Reports",
    "summary": "MRP Reports",
    "description": """
        MRP Reports
    """,
    "author": "Hydra Data and Consulting Ltd",
    "website": "http://www.hydradataandconsulting.co.th",
    "depends": ["base", 'mrp', 'product', 'stock', 'resource'],
    "data": [
        "security/ir.model.access.csv",
        'data/report_paperformat_data.xml',
        "reports/mrp_production_report.xml",
        "reports/hdc_mrp_production_template.xml",
        "reports/hdc_mrp_report_bom_structure.xml",
        "reports/requestion_inventory_ls_report.xml",
        "views/mrp_production_views.xml",

    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
