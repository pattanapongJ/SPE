# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

{
    'name': 'API framework Access and Permissions',
    'summary': """
    """,
    'company': 'EKIKA CORPORATION PRIVATE LIMITED',
    'author': 'EKIKA',
    'website': 'https://ekika.co',
    'category': 'API Tools',
    'version': '14.0.1.0',
    'license': 'OPL-1',
    'depends': ['base', 'web', 'ekika_utils','api_framework_base'],
    'data': [
        'security/ir.model.access.csv',
        'views/easy_api.xml',
        'views/api_custom_control.xml',
        'views/custom_model_access.xml',
        'views/menus.xml',
    ],
    'live_test_url': 'https://youtu.be/gxGNctBO028?si=jiJpxiwIWLfZUF4e',
    'assets': {},
    'images': ['static/description/banner.png'],
    'price': 0.01,
    'currency': 'EUR',
    'description': """
    """
}
