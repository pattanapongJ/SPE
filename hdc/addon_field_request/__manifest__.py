# Copyright 2023 Basic Solution Co.,Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Additional Field Request/Expire Date ",

    'summary': """
        Additional Field Request/Expire Date """,

    'description': """
        Additional Field Request/Expire Date 
    """,

    'author': "Basic Solution Co., Ltd.",
    "category": "Purchase Management",
    'version': '14.0.0.0',
    'depends': ['purchase_request','purchase'],
    'data': [
        'views/purchase_request.xml',
        'views/purchase_order.xml',
    ],
}
