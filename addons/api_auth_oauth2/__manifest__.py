# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

{
    'name': 'API OAuth2 Authentication v14',
    'summary': """You can connect api authentication with OAuth2 Provider.
        OAuth2 authentication Odoo
        OAuth2 Authorization
    """,
    'company': 'EKIKA CORPORATION PRIVATE LIMITED',
    'author': 'EKIKA',
    'website': 'https://ekika.co',
    'category': 'Productivity,Extra Tools,Tools',
    'version': '14.0.1.0',
    'license': 'OPL-1',
    'depends': ['base', 'web', 'api_framework_base', 'auth_oauth'],
    'external_dependencies': {
        'python': ['requests-oauthlib==1.3.1'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/easy_api.xml',
        'views/auth_oauth.xml',
        'views/api_user.xml',
    ],
    'assets': {},
    'images': ['static/description/banner.png'],
    'price': 0.01,
    'currency': 'EUR',
    'description': """
    """
}
