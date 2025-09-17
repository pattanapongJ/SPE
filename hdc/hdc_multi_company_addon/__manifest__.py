# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "HDC Multi Company Addon",
    "summary": "Multi Company Addon",
    "version": "14.0.0.1",
    "category": "Settings",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "license": "AGPL-3",
    "depends": ["web"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_module_category_data.xml",
        "static/src/xml/SwitchCompanyMenu.xml",
    ],
    "qweb": [
        "static/src/xml/base.xml",
    ],
    'bootstrap': True,
}
