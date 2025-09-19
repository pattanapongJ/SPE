{
    'name': 'Unreconcile User Permission',
    'version': '14.0.0.0',
    'category': 'Accounting',
    'author': 'Basic-Solution Co., Ltd.',
    'website': 'https://www.basic-solution.com',
    'summary': '''
        Unreconcile User Permission
    ''',
    'description': 'Unreconcile User Permission',
    'depends': [
        'account',
    ],
    'data': [
        'security/access_security.xml'
    ],
    'qweb': [
        "static/src/xml/account_payment.xml",
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
