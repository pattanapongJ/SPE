{
    'name': 'l10n tax branch in tax invoice & report',
    'version': '14.1.5.2',
    'summary': '''
        showing branch in tax invoice
    ''',
    'category': 'Invoices & Payments',
    'author': 'Basic Solution Co., Ltd.',
    'depends': ['account' ,'branch', 'l10n_th_tax_invoice', 'l10n_th_tax_report'],
    'data': [
        'views/account_move.xml',
        'wizard/tax_report_wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}