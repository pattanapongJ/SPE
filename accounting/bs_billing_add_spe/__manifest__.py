{
    'name': 'Account Billing Salesperson',
    'version': '14.0.2.1.3',
    'category': 'Accounting',
    'author': 'Basic-Solution Co., Ltd.',
    'website': 'https://www.basic-solution.com',
    'summary': '''
        1. Allowing filter billing by Salesperson
        2. Calculating Billing Blance by given percentage
    ''',
    'depends': [
        'account',
        'account_billing', 
        'bs_billing_add',
        'branch',
        'hdc_batch_billing',
        'hdc_billing_period_route',
    ],
    'data': [
        'views/account_billing_view.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}