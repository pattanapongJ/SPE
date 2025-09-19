# -*- coding: utf-8 -*-
{
    'name': 'bs_journal_items_group_account',
    'version': '14.1.1.0',
    'summary': """ Journal items Group By Account""",
    'author': "Basic Solution Co., Ltd.",
    'website': "https://www.basic-solution.com",
    'category': 'Accounting/Accounting',
    'depends': ['account'],
    "data": [
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        "views/res_config_setting.xml",
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
