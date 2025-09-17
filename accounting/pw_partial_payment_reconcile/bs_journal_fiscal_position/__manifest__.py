{
    'name': 'Accounting journal fiscal position',
    'version': '14.0.2',
    'summary': '''
        accounting journal fiscal position
    ''',
    'category': 'Invoivce',
    'author': 'Basic-Solution Co., Ltd.',
    'website': 'https://www.basic-solution.com/',
    'description': "",
    'depends': [
        'account',
    ],
    'data':[
        'views/account_journal.xml',
        'wizard/account_move_reversal_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}