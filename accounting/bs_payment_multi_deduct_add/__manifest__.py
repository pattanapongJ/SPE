# -*- coding: utf-8 -*-
{
    'name': 'bs_payment_multi_deduct_add',
    'version': '14.2.1.0',
    'summary': """ bs_payment_multi_deduct_add """,
    'author': "Basic Solution Co., Ltd.",
    'website': "https://www.basic-solution.com",
    'category': 'Accounting',
    'depends': ['account_payment_multi_deduction','web_m2x_options'],
    "data": [
        "wizard/account_payment_register_views.xml"
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
