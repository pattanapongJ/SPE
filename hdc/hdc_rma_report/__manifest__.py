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
    'name': 'HDC RMA Report',
    'version': '14.0.1.0.1',
    'category': 'Hydra Warehouse',
    'description': """
        HDC RMA Report.
    """,
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    'depends': ['hdc_rma_credit','stock','hdc_rma_dewalt'],

    'data': [
        'security/ir.model.access.csv',
        'data/report_paperformat_data.xml',
        'reports/rma_report.xml',
        'reports/rma_report_template.xml',
        'reports/rma_product_change_report.xml',
        'wizard/wizard_rma_report_view.xml',
        'wizard/wizard_rma_report_list_view.xml',
        'views/crm_claim_ept_view.xml',
        'views/stock_picking_views.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,

}