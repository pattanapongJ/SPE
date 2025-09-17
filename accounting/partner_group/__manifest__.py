{
    'name': 'Patner Group for Contacts',
    'category': 'Sales/CRM',
    'summary': 'modify partner group for contacts',
    'author': 'Basic Solution Co., Ltd',
    'version': '14.2.5',
    'website': 'https://www.basic-solution.com/',
    'depends': ['base','contacts', 'account'],
    'data': [
        'views/menu_item.xml',
        'views/partner_group.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'data/ir_sequence_data.xml',
    ],
    "installable": True,
    'license': 'LGPL-3',
}
