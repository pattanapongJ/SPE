{
    'name': "Bill Payment Status In Purchase",
    'version': "14.0.1.0.0",
    'sequence': -100,
    'depends': ['purchase', 'account'],
    'author': 'Odoo Sphere Solutions',
    'summary': """Bill payment status in purchase form view as well as tree view.""",
    'description': """This module brings an option to see the purchase order's invoice payment status in its corresponding purchase form view as well as tree view.""",
    'data': [
        'views/purchase_inherit.xml',
    ],
    'images': ['static/description/banner.gif'],
    'assets': {
        'web.assets_backend': [
        ],
        'web.assets_frontend': [
        ],
    },
    'application': True,
    'installable': True,
    'auto install': False,
    'license': 'OPL-1',
    'currency': 'USD',
    'price': 3.7,
}
