# -*- coding: utf-8 -*-
{
    'name': "Purchase Team and Access Restriction ",
    'summary': """
Manage purchase orders based on purchase team and roles to access
""",
    'description': """
- Manage multiple purchase teams
- Add team to purchase orders
- Restrict user access other team documents, only access own team documents 
- Team purchase on reporting
    """,
    'author': 'NOS Erp Consulting',
    'version': '14.0.0.1',
    'license': 'OPL-1',
    'price': 00.00,
    'currency': 'USD',
    'support': 'odoo@nostech.vn',
    'images': [
        'static/description/cover.png'
    ],
    'depends': ['account', 'purchase'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/purchase_security.xml',
        # Views
        'views/purchase_team_views.xml',
        'views/purchase_order_views.xml',
    ],
    'auto_install': False,
    'installable': True,
    'category': 'Inventory/Purchase',
    'application': True,
    'sequence': 10,
}
