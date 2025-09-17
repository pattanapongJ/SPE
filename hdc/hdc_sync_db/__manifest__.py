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
    "name": "HDC Sync Database",
    "version": "14.0.1.0.1",
    "category": "API",
    "description": """
        HDC Sync Database M and G.
    """,
    "author": "Hydra Data and Consulting Ltd",
    "website": "http://www.hydradataandconsulting.co.th",
    "depends": ['base', 'mail', 'account'],
    "data": [
        "security/ir.model.access.csv",
        "views/menu_view.xml",
        "views/sync_db_order.xml",
        "views/sync_app_list.xml"

    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": False,
}
