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
    'name': 'HDC Stock Movement',
    'version': '14.0.0.0.1',
    'category': 'HDC',
    'description': """   
    """,
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    'depends': ['report_xlsx','product'],

    'data': [
        'security/ir.model.access.csv',
        'report/report_menu.xml',
        'wizard/wizard_stock_movement_report_view.xml',
        'wizard/wizard_financial_detail_report.xml',
        'wizard/wizard_physical_detail_report.xml',
    ],

    'demo': [],
    'installable': True,
    'auto_install': True,
    'application': True,
}
