# -*- coding: utf-8 -*-
{
    'name': 'Down Payment For Customer and Vendor',
    'version': '14.0.2.1',
    'summary': """ Down Payment For Customer and Vendor """,
    'description': """ Down Payment For Customer and Vendor """,
    'author': "Basic Solution Co., Ltd.",
    'website': "https://www.basic-solution.com",
    'category': 'Accounting/Accounting',
    'depends': ['utm', 'account'],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/ir_sequence_data.xml",
        "views/bs_downpayment_views.xml",
        "views/account_move_views.xml",
        "views/product_template_views.xml"
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
