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
    "name": "HDC Quotation Order",
    "category": "Sale",
    "version": "14.0.0.6",
    "summary": "Addon HDC Quotation Order",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ['base', 'report_xlsx',"sale", "hdc_discount","hdc_sale_remark", "product_bom_revision"],
    "data": [
        "data/sequence.xml",
        "data/report_paperformat_data.xml",
        "security/ir.model.access.csv",
        "views/quotation_views.xml",
        "views/view_quotations.xml",
        "reports/quotation_project_bo_report.xml",
        "reports/quotation_project_depart_report.xml",
        "reports/quotation_th_dis_report.xml",
        "reports/quotation_th_no_dis_report.xml",
        "reports/quotation_en_dis_report.xml",
        "reports/quotation_en_no_dis_report.xml",
        "reports/proforma_en_dis_report.xml",
        "reports/proforma_en_no_dis_report.xml",
        "reports/quotation_report_views.xml",
        "reports/quotation_d_th_dis_report.xml",
        "reports/quotation_d_th_no_dis_report.xml",
        "wizard/wizard_create_sale_order.xml",
        "wizard/wizard_quotation_report_view.xml",
        "wizard/wizard_quotation_change_total_views.xml",
        "wizard/confirm_below_cost_wizard.xml",
        "wizard/wizard_quotation_project_bo.xml",
        "wizard/wizard_quotation_project_department.xml",
        "wizard/approve_below_cost_wizard.xml"
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
