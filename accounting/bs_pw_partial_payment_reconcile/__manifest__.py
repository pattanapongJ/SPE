# -*- coding: utf-8 -*-
{
    'name': 'bs_pw_partial_payment_reconcile',
    'version': '14.0.2.0',
    'summary': """ Displays partial reconcile information """,
    'author': "Basic Solution Co., Ltd.",
    'website': "https://www.basic-solution.com",
    'category': 'Accounting',
    'depends': ['pw_partial_payment_reconcile'],
    "data": [
        "security/ir.model.access.csv",
        "views/assets.xml",
        "views/account_move_views.xml",
        "views/account_payment_views.xml",
        "wizards/partial_payment_wizard.xml",

    ],
    'qweb': [
        "static/src/xml/account_payment.xml",
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
