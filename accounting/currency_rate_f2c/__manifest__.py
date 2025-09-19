# -*- coding: utf-8 -*-
{
    'name': "Foreign Currency to Company Currency",
    'summary': """
        currency exchange rate can be set and calculated from foreign currency to company currency
    """,
    'description': """
        currency exchange rate can be set and calculated from foreign currency to company currency
        货币汇率可以设置并计算外币 to 公司币种，即外币比本位币的汇率
        
    """,
    'author': "zero",
    'category': 'Accounting/Accounting',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_currency_rate.xml',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    # 'post_init_hook': 'load_translations',
}
