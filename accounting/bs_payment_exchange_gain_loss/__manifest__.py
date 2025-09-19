# -*- coding: utf-8 -*-
{
    "name": "To Generate Gain/Loss Entry For Partial Payment",
    "version": "14.0.2.1",
    "description": """ To Generate Gain/Loss Entry For Partial Payment""",
    "summary": """ To Generate Gain/Loss Entry For Partial Payment""",
    "author": "Basic Solution Co., Ltd.",
    "website": "https://www.basic-solution.com",
    "category": "Accounting/Accounting",
    "depends": ["account", "bi_manual_currency_exchange_rate_add"],
    "data": [
        "views/account_move_views.xml",
        "views/account_payment_views.xml",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3",
}
