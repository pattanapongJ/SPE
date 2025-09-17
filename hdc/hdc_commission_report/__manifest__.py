# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'HDC Commission Report',
    'version': '14.0.0.2',
    'category': 'Sale',
    "category": "Warehouse",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "license": "AGPL-3",
    "depends": ["stock", "date_range", "report_xlsx_helper",'hdc_commission','hr'],
    "data": [
        "security/ir.model.access.csv",
        "reports/report_menu.xml",
        "data/initial_data.xml",
        # "data/report_data.xml",
        "views/settle_commissions_view.xml",
        "views/settle_commissions_mall_view.xml",
        "views/commission_report_configuration_view.xml",
        "views/commission_mall_report_configuration_view.xml",
        "wizard/wizard_commission_report_view.xml",
        "wizard/wizard_import_commission_mall_view.xml",
        "wizard/wizard_commission_mall_report_view.xml",
        "views/menu_view.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
