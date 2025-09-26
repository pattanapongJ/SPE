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
    'name': 'HDC Sale Agreement Addon',
    'version': '14.0.0.0.8',
    'category': 'Opendurian WMS',
    'summary': "Sale Agreement Addon",
    'description': """
        Sale Agreement Addon
    """,
    'author': 'Hydra Data and Consulting Ltd.',
    'website': 'http://www.hydradataandconsulting.co.th',
    'depends': ['sale_blanket_order','hdc_sale_project','hdc_sale', 'hdc_sale_type','hdc_sale_agreement_triple_discount','hdc_discount'],

    'data': [
        'security/ir.model.access.csv',
        'views/sale_blanket_order_views.xml',
        'views/sale_view.xml',
        'wizards/wizard_blanket_orders_change_total_views.xml',
        'wizards/wizard_sale_blanket_confirm_view.xml',
        'wizards/create_sale_orders.xml',
    ],

    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
