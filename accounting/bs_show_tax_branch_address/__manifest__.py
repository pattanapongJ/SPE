{
    'name': 'Bs show tax branch address',
    'version': '14.0.0',
    'summary': '''
        Showing tax branch address based on conditions
    ''',
    'category': 'CRM',
    'author': 'Basic-Solution Co., Ltd.',
    'website': 'https://www.basic-solution.com/',
    'description': "",
    'depends': [
        'base',
        'l10n_th_partner',
    ],
    'data':[
        'views/base_address_extended.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}