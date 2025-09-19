# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Invoice Payment Retention",
    "version": "14.2.0.0",
    "category": "Accounting & Finance",
    "summary": "Add retention amount to account move and payment",
    "description": """Migrate version 16 to 14 (Original Version 14.0.1.0.1)""",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/account-invoicing",
    "depends": ["account"],
    "data": [
        "security/security.xml",
        "views/res_config_settings_views.xml",
        "views/account_move_views.xml",
        "wizard/account_payment_register_views.xml",
    ],
    "maintainer": ["kittiu"],
    "installable": True,
    "development_status": "Alpha",
}
