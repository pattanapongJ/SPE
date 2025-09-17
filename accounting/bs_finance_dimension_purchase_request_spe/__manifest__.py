# -*- coding: utf-8 -*-
{
    'name': 'Basic Solution - Finance Dimension Purchase Request For SPE',
    'version': '14.0.0.1',
    'summary': """10 Finance Dimensions For Purchase Request Asset """,
    'author': "Basic Solution Co., Ltd.",
    'website': "https://www.basic-solution.com",
    'category': 'Accounting/Accounting',
    'depends': ['bs_finance_dimension_spe','bs_finance_dimension_purchase_request'],
    "data": [
        "views/purchase_request_views.xml"
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}