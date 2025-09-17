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
    "name": "HDC Product Design Request",
    "category": "MRP",
    "description": """
        Product Design Request
    """,
    "version": "14.0.0.0.1",
    "development_status": "Mature",
    "summary": "Addon HDC MRP Request Hydra",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "license": "AGPL-3",
    "depends": ['hdc_mrp_mr', 'product_cost_security','hdc_product_safetystock','hdc_quotation_order','hdc_addon_product_fields'],
    "data": [
        "security/data.xml",
        "security/ir.model.access.csv",
        "data/master_default_data.xml",
        "views/mrp_pdr_views.xml",
        "views/sale_order_views.xml",
        "views/quotation_views.xml",
        "views/pdr_menu.xml",
        "wizard/wizard_create_mr_views.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
