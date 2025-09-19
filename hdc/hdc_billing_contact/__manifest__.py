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
    "name": "HDC Billing Contact",
    "version": "14.0.0.0.1",
    "category": "Account",
    "summary": "Add Billing Contact",
    "description": """
        Add Billing Contact
    """,
    "author": "Hydra Data and Consulting Ltd",
    "website": "http://www.hydradataandconsulting.co.th",
    "depends": ["hdc_billing_period_route","hdc_company_hydra","hdc_quotation_order","hdc_creditlimit_saleteam"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_billing_place_view.xml",
        "views/account_billing_terms_view.xml",
        "views/account_payment_period_view.xml",
        "views/partner_view.xml",
        "views/quotation_views.xml",
        "views/sale_views.xml",
        "views/account_move_views.xml",
        "views/res_company_views.xml",
        "views/credit_limit_view.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
