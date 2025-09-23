{
    "name": "BS Internal Account Statement Report",
    "version": "14.0.0.0",
    "description": "Reprot for internal account statement report",
    "summary": "",
    "depends": [
        "account",
        "base",
        "hdc_creditlimit_saleteam",
        "crm",
    ],
    "data": [
        "security/ir.model.access.csv",
        "templates/report_template.xml",
        "wizard/internal_account_statement_wizard_view.xml",
        "views/report_menuitem.xml",
        "report/report_action.xml",
        "report/internal_acc_stmt_report.xml",
        "report/report_template.xml",
    ],
    'qweb': ['static/src/xml/report.xml'],
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3"
}