{
    'name': 'BS Select Asset Location And Responsible',
    'version': '14.0.1.0',
    'summary': 'Module to select asset location and responsible person',
    'description': 'This module allows users to select the location and responsible person for assets.',
    'author': "Basic Solution Co., Ltd.",
    'category': 'Accounting',
    'website': "https://www.basic-solution.com",
    'depends': ['account', 'stock', 'hr','account_asset_management'],
    'data': [
        'security/ir.model.access.csv',  # Ensure permissions are set
        'views/asset_location_view.xml',  # Load the modified asset form view
        'views/account_asset_location.xml',  # Load the asset location form view
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
