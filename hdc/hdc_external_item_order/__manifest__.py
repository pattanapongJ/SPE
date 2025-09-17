# Copyright 2025 HYDRA DATA AND CONSULTING CO., LTD. (https://hydradataandconsulting.co.th/)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "HDC External Item Order",
    "summary": "ปรับแก้การท างานดึงข้อมูล External Item Customer",
    "version": "14.0.0.1.0",
    "category": "Sale",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "license": "AGPL-3",
    "depends": [
        "hdc_external_item_customer",
        "hdc_sale_addon",
        "hdc_quotation_order",
        "hdc_sale_agreement_addon",
        "hdc_barcode_spe",
    ],
    "data": [
        'views/multi_external_product_views.xml',
        'views/product_template_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
