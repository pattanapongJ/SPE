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
    'name': 'HDC TMS Hydra',
    'version': '14.0.1.0.1',
    'category': 'Hydra Warehouse',
    'description': """
        TMS from a Central Distribution Warehouse.
    """,
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    'depends': [ 'base', 'stock', 'branch', 'account','hr'],

    'data': [
        'security/ir.model.access.csv',
        'data/distribution_delivery_sequence.xml',
        'views/res_config_settings_views.xml',
        'views/resupply_delivery_round_view.xml',
        'views/resupply_delivery_schedule_view.xml',
        'views/transfer_branch_summary_view.xml',
        'views/distribution_delivery_note_view.xml',
        'wizard/wizard_confirm_delivery_noted_view.xml',
        'views/resupply_menu.xml',        
        'views/billing_status_tms_view.xml',
        'views/delivery_status_tms_view.xml',
        'views/company_delivery_round_view.xml',
        'views/account_move_view.xml',
        'wizard/billing_finance_wizard_view.xml',
        'views/driver_view.xml',
        'views/validate_billing_finance.xml',
        'wizard/wizard_tms_report.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,

}