{
    'name': 'SPE Purchase Receipt list',
    'version': '14.0.0',
    'summary': '''
        Add new menu 'Receipt List'
    ''',
    'category': 'Inventory',
    'author': 'Basic-Solution Co., Ltd.',
    'website': 'https://www.basic-solution.com/',
    'description': "",
    'depends': [
        'purchase'
    ],
    'data':[
        'views/purchase_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}