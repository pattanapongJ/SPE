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
    "name": "HDC Multi Scrap",
    "category": "Hydra Multi Scrap",
    "version": "14.0.1.1.1",
    "summary": "Addon HDC inventory Hydra",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["stock","hdc_confirm_warehouse"],
    "data": [
        "data/ir_sequence_data.xml",
        'data/report_paperformat_data.xml',
        "security/ir.model.access.csv",
        "reports/multi_scrap_views.xml",
        "reports/multi_scrap_report.xml",
        "views/multi_scrap_views.xml",
        "views/stock_picking_views.xml",
        "views/reason_scrap_views.xml",
        "wizard/report_scrap_wizard_view.xml"
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
