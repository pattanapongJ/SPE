# -*- coding: utf-8 -*-
{
    "name": "Filtering Journal List in credit note and debit note forms",
    "version": "14.0.4.0",
    "description": """ Filtering Journal List in credit note and debit note forms """,
    "summary": """ Filtering Journal List in credit note and debit note forms Summary """,
    "author": "Basic Solution Co., Ltd.",
    "website": "https://www.basic-solution.com",
    "depends": ["account", "account_debit_note"],
    "data": [
        "views/account_journal_views.xml",
        "views/account_move_views.xml",
        "wizards/account_debit_note_views.xml",
    ],
    "license": "LGPL-3",
}
