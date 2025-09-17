# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2019 Victor M.M. Torres, Tecnativa SL
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "HDC Purchase Global Discount",
    "version": "14.0.1.1.2",
    "category": "Purchase",
    "license": "AGPL-3",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["purchase", "base","web_tree_dynamic_colored_field"],
    "data": [
        "view/purchase_view.xml",
        "view/account_move_view.xml",
        "security/ir.model.access.csv",
    ],
    "auto_install": False,
    "installable": True,
}

