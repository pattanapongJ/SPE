# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2019 Victor M.M. Torres, Tecnativa SL
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "HDC Landed Cost",
    "version": "14.0.0.0.1",
    "category": "Inventory",
    'summary': "Landed Cost",
    'description': "Landed Cost",
    "license": "AGPL-3",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["stock_landed_costs","hdc_product_hs_code","mrp_landed_costs", "hdc_recalculate_inventory_valuation", "hdc_receipt_list"],
    "data": [
        "security/ir.model.access.csv",
        "reports/report_menu.xml",
        "view/stock_landed_cost_views.xml",
        "view/product_view.xml",
        "wizard/wizard_import_adjustment_manual_line_view.xml",
    ],
    "auto_install": False,
    "installable": True,
}

