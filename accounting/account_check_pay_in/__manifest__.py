# Copyright 2023 Basic Solution Co., Ltd. (www.basic-solution.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Check Pay In",
    "version": "14.0.0.0.2",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Manage deposit of checks to the bank",
    "author": "Basic Solution Co., Ltd.",
    "website": "www.basic-solutioin.com",
    "depends": ["account","sh_pdc","account_menu"],
    "data": [
        "data/sequence.xml",
        "views/account_check_pay_in_view.xml",
        "security/ir.model.access.csv",
        "security/check_pay_in_security.xml",
    ],
    "installable": True,
}
