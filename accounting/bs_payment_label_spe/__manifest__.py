{
    'name': 'BS Payment Label SPE',
    'version': '14.2.0.0.1',
    'category': 'Invoicing',
    'author': 'Basic-Solution Co., Ltd.',
    'website': 'https://www.basic-solution.com/',
    'depends': [
        'account',
        'account_payment_mode',
        'account_payment_multi_deduction',
        'bs_pdc',
        'sh_pdc',
    ],
    'data': [
        'views/account_payment_view.xml',
        'wizard/account_payment_register_view.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}