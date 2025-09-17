# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

{
    'name': 'Odoo Json:API',
    'summary': """
    """,
    'company': 'EKIKA CORPORATION PRIVATE LIMITED',
    'author': 'EKIKA',
    'website': 'https://ekika.co',
    'category': 'Extra Tools,Tools',
    'version': '14.0.1.0',
    'license': 'OPL-1',
    'depends': ['base', 'web', 'api_framework_base', 'api_auth_apikey'],
    'data': [
        'security/ir.model.access.csv',
        'views/easy_api.xml',
        'documentations/easy_jsonapi_doc.xml',
        'wizard/jsonapi_trial_wizard_view.xml',
    ],
    'live_test_url': 'https://youtu.be/gxGNctBO028?si=jiJpxiwIWLfZUF4e',
    'assets': {
        'web.assets_backend': [
            'easy_jsonapi/static/src/**/*',
            'easy_jsonapi/static/src/xml/**/*',
        ]
    },
    'images': ['static/description/banner.png'],
    'price': 0.25,
    'currency': 'EUR',
    'description': """
    """
}
