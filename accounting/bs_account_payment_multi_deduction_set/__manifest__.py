# -*- coding: utf-8 -*-
{
    'name': 'Account Payment Multi Deduction Group',
    'version': '14.0.0.1',
    'summary': """ Account Payment Multi Deduction Group """,
    'category': 'Accounting',
    'author': 'Basic-Solution Co., Ltd.',
    'website': 'https://www.basic-solution.com',
    'depends': ['account_payment_multi_deduct_cost'],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/payment_multi_deduct_group_views.xml",
        "wizard/account_payment_register_views.xml"
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
