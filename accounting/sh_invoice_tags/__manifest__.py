# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

{
    'name': 'Invoice Tags | Bill Tags | Credit Tags | Debit Note Tags',
    'author': 'Softhealer Technologies',
    'website': 'https://www.softhealer.com',
    'license': 'OPL-1',
    'support': 'support@softhealer.com',
    'version': '14.0.6',
    'category': 'Accounting',
    'summary': """
Invoicing Tags Moule, Debit Note Tag App, Credit Note Tags,
Bill Tags, Refund Tags, Journal Items Tag, Journal Entry Tags,
Invoice Analytics Odoo
""",
    'description': """
This module enables the feature to create accounting tags
(invoice, bill, credit note, debit note, refund, journal entry,
journal item) tags. You can change the color of tags as per need.
You can filter invoice records using particular tags.
You can search the records using tags also.
""",
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'security/mass_tag_update_rights.xml',
        'views/invoice_tags_view.xml',
        'views/invoice_view.xml',
        'views/invoice_journals_item_view.xml',
        'views/mass_tag_update_wizard_view.xml',
        'views/mass_tag_update_action.xml',
        'views/default_tags_configuration.xml',
        ],
    'images': ['static/description/background.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': '15',
    'currency': 'EUR',
    }
