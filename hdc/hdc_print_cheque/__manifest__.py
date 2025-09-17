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
    "name": "HDC Print Cheque",
    "author": "Hydra Data and Consulting Ltd",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Accounting",
    "summary": "Print Cheque Bank",
    "version": "14.0.0.0.1",
    "depends": [
        "sh_pdc",
        "l10n_th_tax_invoice"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/report_paperformat_data.xml",
        "report/reports_cheque.xml",
        "report/report_cheque_ttb.xml",
        "report/report_cheque_scb.xml",
        "report/report_cheque_uob.xml",
        "report/report_cheque_kbank.xml",
        "report/report_cheque_lhb.xml",
        "report/report_cheque_bbl.xml"
    ],
    "application": True,
    "auto_install": False,
    "installable": True,
}