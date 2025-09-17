# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2019 Victor M.M. Torres, Tecnativa SL
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "HDC Sale",
    "version": "14.0.1.1.0",
    "category": "Sale",
    "license": "AGPL-3",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["sale" , "base", "sale_stock", "hdc_partner_delivery_line",'account'],
    "data": [
        "view/sale_view.xml",
        "view/account_move_views.xml",
        "security/ir.model.access.csv",
    ],
    "auto_install": False,
    "installable": True,
}

