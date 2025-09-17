# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

{
    'name': 'GraphQL API for Odoo',
    'summary': """
    """,
    'company': 'EKIKA CORPORATION PRIVATE LIMITED',
    'author': 'EKIKA',
    'website': 'https://ekika.co',
    'category': 'Productivity,Tools',
    'version': '14.0.1.0',
    'license': 'OPL-1',
    'depends': ['base', 'web', 'api_framework_base', 'api_auth_apikey'],
    'external_dependencies': {
        'python': ['graphql-core==3.1.5'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/easy_api.xml',
        'documentation/easy_graphql_doc.xml',
    ],
    'live_test_url': 'https://youtu.be/gxGNctBO028?si=jiJpxiwIWLfZUF4e',
    'assets': {},
    'images': ['static/description/banner.png'],
    'price': 0.25,
    'currency': 'EUR',
    'description': """
    """
}
