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
    "name": "HDC Add Form No.",
    "version": "14.0.0.0.1",
    "category": "Account",
    "summary": "Add Form No. In Many Place In Account",
    "description": """
        Add Form No. In Many Place In Account
    """,
    "author": "Hydra Data and Consulting Ltd",
    "website": "http://www.hydradataandconsulting.co.th",
    "depends": ["account_billing",'account','hdc_creditlimit_saleteam','hdc_sale_type_internal_transfer','hdc_tms'],
    "data": [
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        "views/account_billing_views.xml",
        "views/account_payment_view.xml"
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
