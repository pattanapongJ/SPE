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
    'name': 'HDC Pricelist Shipping Cost',
    'version': '14.0.0.0.1',
    'category': 'Sale',
    'summary': "Sale",
    'description': """
        Pricelist Shipping Cost
    """,
    'author': 'Hydra Data and Consulting Ltd.',
    'website': 'http://www.hydradataandconsulting.co.th',
    'depends': [
        'hdc_discount', 'sale_pricelist_item_advanced', 
        'product',
        'hdc_sale_triple_discount','uom_in_pricelist', 'hdc_quotation_order_finance_dimension', 'hdc_quotation_order',
        'sale_blanket_order'],
    'data': [
        'views/product_pricelist_views.xml',
        'views/sale_view.xml',
        'views/product_template.xml',
        'views/view_quotations.xml',
        'views/sale_blanket_order_views.xml',
        'wizard/wizard_create_sale_order.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
