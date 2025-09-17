{
    'name': 'Account Billing Group',
    'version': '14.0.1.1',
    'category': 'Accounting',
    'author': 'Basic-Solution Co., Ltd.',
    'website': 'https://www.basic-solution.com',
    'depends': ['mail', 'account', 'branch',],
    'data': [
        'data/billing_sequence.xml',
        'security/ir.model.access.csv',
        'views/account_group_billing_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}