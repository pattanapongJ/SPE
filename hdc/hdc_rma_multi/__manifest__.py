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
    'name': 'HDC RMA Multiple Hydra',
    'version': '14.0.1.0.1',
    'category': 'Hydra Warehouse',
    'description': """
        HDC RMA Multiple Hydra.
    """,
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    'depends': ['rma_ept','hdc_inventory_config','hdc_external_item_customer','hdc_add_from_no_header'],

    'data': [
        'data/ir_sequence.xml',
        'data/addition_operation_type_data.xml',
        'data/report_paperformat_data.xml',
        'security/ir.model.access.csv',
        'reports/crr_report.xml',
        'reports/crr_report_template.xml',
        'reports/crr_report_template_a5.xml',
        'wizard/wizard_crr_report_view.xml',
        'wizard/wizard_create_multi_rma_view.xml',
        'wizard/wizard_add_product_crr_view.xml',
        'wizard/wizard_confirmation_crr_view.xml',
        'views/stock_location_view.xml',
        'views/receive_method_view.xml',
        'views/customer_return_request_view.xml',
        'views/crm_claim_ept_view.xml',
        'views/stock_picking_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,

}