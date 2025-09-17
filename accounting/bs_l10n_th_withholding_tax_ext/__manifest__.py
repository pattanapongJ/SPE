# -*- coding: utf-8 -*-
{
    "name": "bs_l10n_th_withholding_tax_ext",
    "version": "14.2.0.0",
    'description': """ rounding different amount """,
    'summary': """ bs_l10n_th_withholding_tax_ext  """,
    'author': "Basic Solution Co., Ltd.",
    'website': "https://www.basic-solution.com",
    'category': 'Report',
    'depends': ['l10n_th_withholding_tax_cert','l10n_th_withholding_tax_multi'],
    "data": [
        "security/rule_security.xml",
        "views/account_withholding_tax_views.xml",
        "views/product_views.xml",
        "views/withholding_tax_cert_views.xml"
    ],
    'license': 'LGPL-3',
}
