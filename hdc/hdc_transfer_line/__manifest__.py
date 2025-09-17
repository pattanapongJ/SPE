# Copyright 2025 HYDRA DATA AND CONSULTING CO., LTD. (https://hydradataandconsulting.co.th/)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "HDC Internal Line",
    "summary": "รายการหยิบสินค้าแยกระหว่าง คลังสินค้า 4 และคลังสินค้า 5",
    "version": "14.0.1.0.0",
    "category": "Warehouse",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "license": "AGPL-3",
    "depends": [
        "hdc_inventory_config",
        "hdc_inventory_general_report",
        "hdc_sale_type",
        "hdc_sale_quick_invoice",
        "hdc_confirm_warehouse",
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/transfer_line_views.xml',
        'views/operation_type_views.xml',
        'reports/transfer_line_report.xml',
        'reports/report_views.xml',

        'views/menu_views.xml',
    ],
    #'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
    'application': True,
}
