# -*- coding: utf-8 -*-
{
    'name': 'BS PDC SPE',
    'version': '14.0.1.0',
    'summary': """ BS PDC SPE """,
    'author': "Basic Solution Co., Ltd.",
    'website': "https://www.basic-solution.com",
    'category': 'Accounting',
    'depends': ['bs_customer_bank_account_spe','bs_pdc','bs_bank_account_type'],
    "data": [
        "views/pdc_wizard_views.xml",
        "views/res_partner_bank_views.xml",
        "views/account_payment_register_views.xml",
        "views/account_payment_views.xml"
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
