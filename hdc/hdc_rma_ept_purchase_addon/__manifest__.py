# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
{

    # App information
    'name': 'Purchase-RMA (Return Merchandise Authorization) Addon in Odoo',
    'version': '14.0.0.1',
    'category': 'RMA',
    'license': 'OPL-1',
    'summary': "Manage Return Merchandize Authorization (RMA) Addon in Odoo",

    # Author
    'author': 'Hydra Data and Consulting Ltd',
    'website': "http://www.hydradataandconsulting.co.th",

    # Dependencies
    'depends': ['hdc_rma_ept_purchase'],

    'data': [
        'security/ir.model.access.csv',
        'views/crm_claim_ept_view.xml',
    ],


    # Technical
    'installable': True,
    'auto_install': False,
    'application': True,
    'active': False,

}
