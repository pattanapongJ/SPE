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
    "name": "HDC Claims Management Report",
    "category": "Customer Relationship Management",
    "version": "14.0.0.1",
    "summary": "Addon Claims Management Report",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["crm_claim_code"],
    "data": [
        "data/report_paperformat_data.xml",
        "security/ir.model.access.csv",
        "views/crm_claim_view.xml",
        "report/crm_claim_report_template.xml",
        "report/crm_claim_report.xml",
        "wizard/wizard_crm_claim_report_view.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
