# Copyright 2015-2021 Tecnativa - Pedro M. Baeza
# Copyright 2017 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Supplier invoices on HR expenses",
    "version": "14.0.1.0.0",
    "category": "Human Resources",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/hr-expense",
    "depends": ["base","hr_expense","hr_expense_number_unique"],
    "data": [
        "data/report_paperformat_data.xml",
        "views/hr_expense_views.xml",
        "report/hr_expense_report_views.xml",
        "report/expense_report.xml",
    ],
    "installable": True,
}
