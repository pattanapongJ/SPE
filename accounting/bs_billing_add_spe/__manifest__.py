{
    'name': 'Account Billing Salesperson',
    'version': '14.0.2.1.4',
    'category': 'Accounting',
    'author': 'Basic-Solution Co., Ltd.',
    'website': 'https://www.basic-solution.com',
    'summary': '''
        1. Allowing filter billing by Salesperson
        2. Calculating Billing Blance by given percentage
    ''',
    'depends': [
        'account_billing', 
        'bs_billing_add',
        'branch',
    ],
    'data': [
        'views/account_billing_view.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}