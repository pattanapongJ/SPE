# -*- coding: utf-8 -*-
{
    "name": "Currency Exchange Rate on Invoice/Payment/Sale/Purchase in Odoo with Inverse Rate",
    "version": "14.2.1.0",
    "description": """ Currency Exchange Rate on Invoice/Payment/Sale/Purchase in Odoo with Inverse Rate """,
    "summary": """ Currency Exchange Rate on Invoice/Payment/Sale/Purchase in Odoo with Inverse Rate  """,
    "author": "Basic Solution Co., Ltd.",
    "website": "https://www.basic-solution.com",
    "category": "Accounting",
    "depends": ["bi_manual_currency_exchange_rate"],
    "data": [
        "views/account_move_view.xml",
        "views/account_payment_view.xml",
        "views/purchase_view.xml",
        "views/sale_view.xml",
    ],
    "license": "LGPL-3",
}
