# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2019 Victor M.M. Torres, Tecnativa SL
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "HDC Sale Addon",
    "version": "14.0.0.0.7",
    "category": "Sale",
    'summary': "Sale Addon",
    'description': "Sale Addon",
    "license": "AGPL-3",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["hdc_sale","sale_order_type","hdc_deduct_down_payments","hdc_product_kit","sales_team"],
    "data": [
        "security/ir.model.access.csv",
        "view/sale_view.xml",
        "view/account_move_view.xml",
        "view/crm_tag_view.xml",
        "wizard/sale_make_invoice_advance_views.xml",
    ],
    "auto_install": False,
    "installable": True,
}

