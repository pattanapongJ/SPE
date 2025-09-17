{
    "name": "Payment Register with Multiple Deduction Cost Center",
    "version": "14.2.1.0",
    'author': 'Basic-Solution Co., Ltd.',
    'website': 'https://www.basic-solution.com/',
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": ["account", "account_payment_multi_deduction", "sh_cost_center", "account_asset_management"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/account_payment_register_views.xml",
        "views/account_asset_view.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
}
