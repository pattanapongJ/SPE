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
    'name': 'HDC Cancel Sale and Pickinglist By Line',
    'version': '14.0.1',
    'category': 'Sale',
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    'description': """
        HDC Cancel Sale By Line
    """,
    'depends': ['hdc_auto_cancel_invoice','hdc_promotion_priority','hdc_inventory_picking_list_sale'],
    'data': [
        'security/ir.model.access.csv',
        'view/sale_views.xml',
        'view/stock_picking_view.xml',
        'wizard/wizard_cancel_so_line.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
###################################################################################
