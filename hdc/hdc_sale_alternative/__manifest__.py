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
    "name": "HDC Sale Agreement Alternative Product",
    "category": "Sale",
    "description": """
        Sale Agreement alternative product
    """,
    "version": "14.0.1.1.1",
    "development_status": "Mature",
    "summary": "Addon HDC CRM Hydra",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "license": "AGPL-3",
    "depends": ["sale","base","product","sale_blanket_order"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/alternative_product_wizard.xml",
        "wizard/low_stock_wizard.xml",
        "views/sale_view.xml",
        "views/product_view.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
