# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "HDC Stock Card Report",
    "summary": "Add stock card report and view on Inventory Reporting. ",
    "version": "14.0.0.1.0",
    "category": "Warehouse",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "license": "AGPL-3",
    "depends": ["stock", "date_range", "report_xlsx_helper",'product','hdc_on_the_way','stock_picking_invoice_link','product'],
    "data": [
        "security/ir.model.access.csv",
        "data/report_data.xml",
        "reports/stock_movement_report.xml",
        "reports/financial_detail_report.xml",
        "reports/financial_detail_report_summary.xml",
        "reports/physical_detail_report.xml",
        "reports/physical_detail_report_summary.xml",
        "reports/report_menu.xml",
        "wizard/wizard_stock_movement_report_view.xml",
        "wizard/wizard_financial_detail_report.xml",
        "wizard/wizard_financial_detail_report_summary.xml",
        "wizard/wizard_physical_detail_report.xml",
        "wizard/wizard_physical_detail_report_summary.xml",
    ],
    'installable': True,
    'auto_install': True,
    'application': True,
}
