# -*- coding: utf-8 -*-
{
    'name': 'Bs_l10n_th_tax_report',
    'version': '14.0.6.3',
    'summary': """ Bs_l10n_th_tax_report Summary""",
    'author': "Basic Solution Co., Ltd.",
    'website': "https://www.basic-solution.com",
    'category': 'Accounting/Accounting',
    'depends': ['l10n_th_tax_report','bs_tax_branch','date_range','bs_branch_address_add'],
    "data": [
        "views/date_range_views.xml",
        "report/tax_report.xml"
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
