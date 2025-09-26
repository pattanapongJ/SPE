# -*- coding: utf-8 -*-
{
    "name": "bs_po_type_pr",
    "version": "14.0.0.0.1",
    'description': """ BS Purchase Order Type """,
    'summary': """  BS Purchase Order Type  """,
    'author': "Basic Solution Co., Ltd.",
    'website': "https://www.basic-solution.com",
    'category': 'Inventory/Purchase',
    'depends': ['purchase_request','purchase_order_type', 'receipt_operation_type'],
    'data': [
        'views/purchase_request_view.xml',
        'wizard/purchase_request_line_make_purchase_order_view.xml'
    ],
    'license': 'LGPL-3',
}
