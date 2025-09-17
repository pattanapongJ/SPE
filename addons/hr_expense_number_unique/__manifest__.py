# -*- coding: utf-8 -*-
# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Expense Unique Number Sequence',
    'version': '1.1.2',
    'category': 'Human Resources/Expenses',
    'price': 9.0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'depends': [
        'hr_expense'
    ],
    'summary': 'Unique Sequence Number of Expense / Expense Sheet',
    'description': """
This app auto generates sequence numbers for expenses and expense sheets as shown below.
    """,
    'author': "Probuse Consulting Service Pvt. Ltd.",
    'website': "http://www.probuse.com",
    'live_test_url': 'http://probuseappdemo.com/probuse_apps/hr_expense_number_unique/308',#'https://youtu.be/wnwFijTFglk',
    'support': 'contact@probuse.com',
    'images': ['static/description/display.jpg'],
    'data': [
        'data/ir_sequence_data.xml',   
        'views/hr_expense_views.xml',
        'views/hr_expense_sheet_views.xml',    
        ],
    'installable': True,
    'application': False,
}
