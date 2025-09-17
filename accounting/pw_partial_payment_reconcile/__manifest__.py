# -*- coding: utf-8 -*-
{
    'name': 'Account Partial Payment Reconcile',
    'version': '14.2.0.0',
    'author': 'Preway IT Solutions',
    "sequence": 2,
    'category': 'Accounting',
    'depends': ['account'],
    'summary': 'This module is allow you to partial payment reconcile in Invoice, Bills, Credit Note and Refunds | Partial Payment Reconciliation and Unreconciliation | Imvoice Partial Payment | Bill Partial Payment | Credit Note Partial Payment | Refund Partial Payment | Partial Refund | Add Partial Payment',
    'description': """
  Partial Payment Reconciliation and Unreconciliation (Original V1.0)
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'wizard/partial_payment_wizard.xml',
    ],
    'qweb': [
        "static/src/xml/account_payment.xml",
    ],
    'price': 40.0,
    'currency': "EUR",
    'application': True,
    'installable': True,
    "auto_install": False,
    'live_test_url': 'https://youtu.be/h2W6uSjACNA',
    "images":["static/description/Banner.png"],
}
