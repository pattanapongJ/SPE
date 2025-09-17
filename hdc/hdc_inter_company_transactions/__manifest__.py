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
    "name": "HDC Inter Company Transactions",
    "category": "Sale",
    "version": "14.0.0.1",
    "summary": "Addon HDC Inter Company Transactions",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["purchase","purchase_order_type","hdc_sale_type","product","hdc_sale","hdc_tms","dev_customer_credit_limit"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_view.xml",
        "views/purchase_order_type_view.xml",
        "views/product_supplierinfo_view.xml",
        "views/product_template_view.xml",
        "views/partner_view.xml",
        "data/initial_data.xml",
        "report/inter_company_report_views.xml",
        "wizard/wizard_sale_inter_company_view.xml",
        "wizard/wizard_sale_inter_company_report.xml",
        "wizard/wizard_sale_po_inter_company_report.xml",
        "wizard/wizard_sale_inter_company_warning.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
