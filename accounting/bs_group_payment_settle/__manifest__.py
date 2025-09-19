# -*- coding: utf-8 -*-
{
    'name': 'Group Payment Settle',
    'version': '0.1.0',
    'summary': """ Group Payment Settle """,
    'author': "Basic Solution Co., Ltd.",
    'website': "https://www.basic-solution.com",
    'category': 'Accounting',
    'depends': ['account','bs_payment_multi_deduct_add','bi_manual_currency_exchange_rate_add'],
    "data": [
        "security/ir.model.access.csv",
        "wizard/account_payment_register_views.xml"
    ],
    
    'license': 'LGPL-3',
}
