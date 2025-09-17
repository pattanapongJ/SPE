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
    "name": "HDC Inventory Configuration",
    "version": "14.0.1.0.1",
    'category': 'SATR',
    "summary" : "Inventory Configuration SATR",
    "author": "Hydra Data and Consulting Ltd",
    "website": "http://www.hydradataandconsulting.co.th",
    "depends": ["base", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/addition_operation_type_data.xml",
        "views/operation_type_inherit.xml",
        "views/addition_operation_type_view.xml",
    ],
    "demo": [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
