# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2019 Victor M.M. Torres, Tecnativa SL
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "HDC Master Inventory Adjust Type",
    "version": "14.0.0.0.2",
    "category": "Inventory",
    'summary': "Inventory Adjust Type",
    'description': "Inventory Adjust Type",
    "license": "AGPL-3",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["stock","hdc_inter_transfer","hdc_inventory_borrow"],
    "data": [
        "security/ir.model.access.csv",
        'view/inventory_inter_transfer_type_views.xml',
        "view/inventory_borrow_type_views.xml",
        "view/stock_picking_views.xml"
    ],
    "auto_install": False,
    "installable": True,
}

