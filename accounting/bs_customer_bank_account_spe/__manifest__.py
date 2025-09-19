# -*- coding: utf-8 -*-
{
    'name': 'Bs_customer_bank_account_spe',
    'version': '14.0.1.0',
    'summary': """ Bs_customer_bank_account_spe Summary """,
    'author': "Basic Solution Co., Ltd.",
    'website': "https://www.basic-solution.com",
    'category': 'Accounting/Accounting',
    'depends': ['bs_pdc'],
    "data": [
        "views/account_payment_views.xml",
        "views/account_payment_register_views.xml",
        "views/pdc_wizard_views.xml"
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
