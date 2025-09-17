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
    "name": "HDC Deduct Down Payments",
    "category": "RMA",
    "description": """
        Deduct Down Payments
    """,
    "version": "14.0.0.0.1",
    "summary": "Deduct Down Payments",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "license": "AGPL-3",
    "depends": ["account","sale","base","hdc_billing_period_route"],
    "data": [
        "security/ir.model.access.csv",
        # "wizard/crm_lead_lost_views.xml",
        'wizard/sale_make_invoice_advance_views.xml',
        "views/sale_views.xml",
        "views/account_move_views.xml",
        "views/res_config_settings_views.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
