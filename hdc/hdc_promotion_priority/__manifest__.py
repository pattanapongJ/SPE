# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2019 Victor M.M. Torres, Tecnativa SL
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "HDC Priority Promotion",
    "version": "14.0.1.1.0",
    "category": "Sale",
    "license": "AGPL-3",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["sale_coupon","hdc_sale_exclude_taxes","hdc_sale_general_reports","hdc_promotion_free"],
    "data": [
        "security/ir.model.access.csv",
        "views/coupon_program_views.xml",
        "views/sale_view.xml",
        "views/account_move_view.xml",
    ],
    "auto_install": False,
    "installable": True,
}

