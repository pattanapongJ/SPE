{
    'name': 'Purchase request report',
    'version': '14.0.2',
    'category': 'Inventory',
    'author': 'Basic-Solution Co., Ltd.',
    'depends':['purchase_request', 'product','partner_fax'],
    'data': [
        'report/report_purchase_request.xml',
        'report/purchase_template.xml',
        'report/request_report.xml',
        'views/product_template_view.xml',
        'views/purchase_request_view.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',

}