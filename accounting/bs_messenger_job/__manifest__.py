# -*- coding: utf-8 -*-
{
    'name': 'BS Messagender Job',
    'version': '14.0.1.0',
    'summary': """ BS Messenger Job """,
    'author': "Basic Solution Co., Ltd.",
    'website': "https://www.basic-solution.com",
    'category': 'Accounting',
    'depends': ['account','account_billing','hdc_batch_billing'],
    "data": [
        "security/ir.model.access.csv",
        "data/data_sequence.xml",
        "views/batch_billing.xml",
        "views/messenger_job_view.xml",
        "views/menuitem.xml",
        "wizard/multiple_selection_form.xml",
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
