{
    'name': 'Product Category Extension/Technical Module',
    "version": "14.0.1",
    "license": "AGPL-3",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    'description': """
        Define group by product cetogory   
    """,
       "depends": ["product","product_category_code","product_category_code_unique","stock"
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/initial_data.xml',
        'views/product_category_level.xml',
             ],
    'installable': True,
    'auto_install': False,
    'application': True,
}