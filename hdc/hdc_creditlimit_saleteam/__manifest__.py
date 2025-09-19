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
{
    'name': 'HDC Credit Limit Sale Team',
    'version': '14.0.2',
    'category': 'Sale',
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    'description': """
        HDC Credit Limit Sale Team
    """,
    'depends': ['base', 'sale', 'sale_order_type', 'dev_customer_credit_limit', 'account','hdc_quotation_order','sale_blanket_order','is_customer_is_vendor','hdc_sale_agreement_addon','hdc_sale_line_detail'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence.xml',
        'data/report_paperformat_data.xml',
        'data/ir_cron_data.xml',
        'views/credit_limit_request.xml',
        'views/customer_credit_limit_view.xml',
        'views/credit_limit_view.xml',
        'views/res_config_settings_views.xml',
        'views/sale_view.xml',
        'views/partner_view.xml',
        'views/account_move_views.xml',
        'views/quotation_views.xml',
        'views/sale_blanket_order_views.xml',
        'views/menu_view.xml',
        'report/creditlimit_request_report.xml',
        'report/creditlimit_report_views.xml',
        'report/creditlimit_request_single_report.xml',
        'report/creditlimit_request_multi_report.xml',
        'wizard/customer_limit_wizard_view.xml',
        'wizard/below_cost_warning_wizard.xml',
        'wizard/wizard_temp_credit_request_report_view.xml',
        'wizard/wizard_temp_credit_request_report_multi_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'post_init_hook': 'post_init_hook',
}
###################################################################################
