# -*- coding: utf-8 -*-
{
    'name': "Bank Statement Reconciliation",

    'summary': 'Reconciliation, Bank Reconciliation, Invoice Reconciliation, Payment Reconciliation, Bank Statement',
    
    'description' : """
        * Bank Statement Reconciliation (odoo 14)
    """,

    "author": "Openinside",
    "license": "OPL-1",
    'website': "https://www.open-inside.com",
    "price" : 100,
    "currency": 'USD',
    'category': 'Accounting',
    'version': '14.0.1.1.4',

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        'views/account_bank_statement.xml',
        'views/account_bank_statement_line.xml',
        'views/account_payment.xml',
        'views/account_move_line.xml',
        'views/account_journal.xml',        
        'views/account_bank_statement_generate.xml',
        'views/menu.xml',
        'security/ir.model.access.csv',        
    ],    
    'odoo-apps' : True,
    'auto_install': True,
    'images': [
        'static/description/cover.png'
    ],    
}