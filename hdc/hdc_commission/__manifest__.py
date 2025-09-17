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
    'name': 'HDC Commission',
    'version': '14.0.0.2',
    'category': 'Sale',
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    'description': """
        HDC Commission
    """,
    'depends': ['base', 'sale','account','product','hdc_multi_company_addon','is_customer_is_vendor','bs_pw_partial_payment_reconcile','hdc_add_from_no_header'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_module_category_data.xml',
        'data/ir_sequence.xml',
        'data/initial_data.xml',
        'views/generate_settle_commissions_view.xml',
        'views/settle_commissions_view.xml',
        'views/commission_type_view.xml',
        'views/generate_settle_commissions_mall_view.xml',
        'views/settle_commissions_mall_view.xml',
        'views/product_view.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
        'views/update_commission_code_view.xml',
        'views/menu_view.xml',
        'wizard/wizard_create_settlements_view.xml',
        'wizard/wizard_create_settlements_mall_view.xml',
        'wizard/wizard_update_commission_code_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
###################################################################################
