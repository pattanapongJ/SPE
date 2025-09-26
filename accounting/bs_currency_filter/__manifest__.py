# -*- coding: utf-8 -*-
{
    'name': 'BS Currency Filter',
    'version': '14.0.0.0',
    'summary': """ BS Currency Filter For Sale,Purchase """,
    'author': "Basic Solution Co., Ltd.",
    'website': "https://www.basic-solution.com",
    'category': 'Accounting/Accounting',
    'depends': ['base','sale_management','purchase','account','hr_expense'],
    "data": [
        "views/res_currency_views.xml",
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
