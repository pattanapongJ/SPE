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
    'name': 'HDC Plan Purchase Forecast Addon',
    'version': '14.0.0.0.3',
    'category': 'Sale',
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    'description': """
        HDC Plan Purchase Forecast Addon
    """,
    'depends': ['hdc_plan_purchase_forecast','hdc_mrp_mr','hdc_product_addon_fields'],
    'data': [
        "data/scheduled_actions.xml",
        "data/partner_data.xml",
        "security/ir.model.access.csv",
        "views/product_view.xml",
        "views/search_template.xml",
        "views/search_forecast_purchase.xml",
        "wizard/request_for_quotation_wizard_view.xml",
        "wizard/request_for_mrp_request_wizard_view.xml",
    ],
    'qweb': [
        'static/src/xml/search_purchase_forecast.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
###################################################################################
