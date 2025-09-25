
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
    "name": "HDC Account Invoice Reports",
    "version": "14.0.1.1.13",
    "category": "Invoice Reports",
    "summary": "Account Invoice Reports",
    "description": """
        Account Invoice Reports
    """,
    "author": "Hydra Data and Consulting Ltd",
    "website": "http://www.hydradataandconsulting.co.th",
    "depends": ["base", "account", "account_billing", "sale", "l10n_th_tax_invoice","hdc_discount","hdc_batch_billing"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/wizard_invoice_report_view.xml",
        "data/report_paperformat_data.xml",
        "report/invoice_report.xml",
        "report/bill_invoice_report.xml",
        "report/tax_invoice_report.xml",
        "report/receipt_invoice_report.xml",
        "report/credit_invoice_report.xml",
        "report/debit_invoice_report.xml",
        "report/account_report_views.xml",
        "report/payment_voucher_report.xml",
        "report/receipt_voucher_report.xml",
        "report/delivery_item_report.xml",
        "report/tax_invoice_affiliated_company_report.xml",
        "report/report_billing_a4.xml",
        "report/report_billing_retail.xml",
        "report/report_billing_percent.xml",
        "report/report_billing_preprint.xml",
        "report/tax_invoice_abb_report.xml",
        "report/pos_invoice_report.xml",
        "report/general_voucher_report.xml",
        "report/pre_print_voucher_report.xml",
        "report/payment_receipt_invoice_report.xml",
        "report/credit_note_report.xml",
        "report/debit_note_report.xml",
        "report/batch_billing_report.xml",
        "report/batch_billing_total_report.xml",
        "report/account_receipt_invoice_report.xml",
        "report/account_receipt_invoice_report2.xml",
        "report/vb_bill_pre_report.xml",
        "report/invoice_borrow_report.xml",
        "views/account_move_view.xml",
        "views/account_payment_view.xml",
        "views/product_views.xml",
        "views/sale_view.xml",
        "views/template.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": True,
}