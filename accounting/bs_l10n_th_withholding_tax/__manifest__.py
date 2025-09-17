# -*- coding: utf-8 -*-
{
    'name': 'bs_l10n_th_withholding_tax',
    'version': '14.0.0.1',
    'summary': """ bs_l10n_th_withholding_tax""",
    'category': 'Accounting',
    'author': 'Basic-Solution Co., Ltd.',
    'website': 'https://www.basic-solution.com',
    'depends': ['account','l10n_th_withholding_tax','bs_l10n_th_withholding_tax_ext',],
    "data": [
        "views/withholding_type.xml",
        'views/account_move_line_views.xml',
        'views/withholding_tax_branch.xml',
    ],
    'license': 'LGPL-3',
}
