{
    'name': 'Account billing show total amount',
    'version': '14.4.4',
    'category': 'Accounting',
    'author': 'Basic-Solution Co., Ltd.',
    'depends': ['base', 'web','account_billing'],
    'data': [
        'views/account_billing_view.xml',
        'templates/assets.xml',
        'views/account_move_view.xml',
    ],
    'post_init_hook': 'update_existing_payment_terms',
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}