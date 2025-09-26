# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2019 Victor M.M. Torres, Tecnativa SL
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "HDC Inventory Adjust Type",
    "version": "14.0.0.0.2",
    "category": "Inventory",
    'summary': "Inventory Adjust Type",
    'description': "Inventory Adjust Type",
    "license": "AGPL-3",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["stock"],
    "data": [
        "data/ir_sequence.xml",
        "security/ir.model.access.csv",
        "view/inherited_stock_inventory.xml"
    ],
    "auto_install": False,
    "installable": True,
}

