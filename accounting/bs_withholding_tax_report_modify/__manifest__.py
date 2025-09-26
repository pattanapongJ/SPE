# -*- coding: utf-8 -*-
{
    "name": "Basics Withholding Tax Report Modify",
    'version': '14.0.0.1',
    'description': """ Thai Localization - Expense Withholding Tax """,
    'summary': """ l10n_th_withholding_tax_report """,
    'author': "Basic Solution Co., Ltd.",
    'website': "https://www.basic-solution.com",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": [
        "account",
        "report_xlsx_helper",
        "date_range",
        "l10n_th_partner",
        "l10n_th_withholding_tax_cert",
        "l10n_th_withholding_tax_report",
    ],
    "data": [
        "templates/report_template.xml",
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
