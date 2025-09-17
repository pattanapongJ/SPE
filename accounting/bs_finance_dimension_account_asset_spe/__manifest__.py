# -*- coding: utf-8 -*-
{
    'name': 'Basic Solution - Finance Dimension Account Asset For SPE',
    'version': '14.0.0.0',
    'summary': """10 Finance Dimensions For Account Asset """,
    'author': "Basic Solution Co., Ltd.",
    'website': "https://www.basic-solution.com",
    'category': 'Accounting/Accounting',
    'depends': ['bs_finance_dimension_spe','bs_finance_dimension_account_asset'],
    "data": [
        'views/account_asset_views.xml'
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
