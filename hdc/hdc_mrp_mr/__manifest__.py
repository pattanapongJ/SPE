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
    "name": "HDC MRP Request",
    "category": "MRP",
    "description": """
        MRP Request
    """,
    "version": "14.0.0.0.0",
    "development_status": "Mature",
    "summary": "Addon HDC MRP Request Hydra",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "license": "AGPL-3",
    "depends": ["sale","mrp","base","stock","hdc_inter_transfer_addon_field","hdc_product_safetystock","account"],
    "data": [
        "security/ir.model.access.csv",
        "security/groups.xml",
        "data/master_default_data.xml",
        "data/report_paperformat_data.xml",
        "report/mrp_mr_report.xml",
        "report/mr_report.xml",
        "views/mrp_mr_views.xml",
        "views/request_tyre_mr_views.xml",
        "views/product_tyre_mr_views.xml",
        "views/mrp_workcenter_views.xml",
        "views/mrp_production_views.xml",
        "views/mrp_bom_view.xml",
        "views/mr_menu.xml",
        "wizard/wizard_mrp_to_inter_view.xml",
        "wizard/wizard_create_mo_view.xml",
        "wizard/wizard_mr_product_receive_view.xml",
        "wizard/wizard_mrp_to_inter_factory_view.xml",
        "wizard/wizard_create_mo_modify_view.xml",
        "wizard/wizard_mrp_to_inter_modify_view.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
