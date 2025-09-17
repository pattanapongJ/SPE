# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2019 Victor M.M. Torres, Tecnativa SL
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "HDC Global Discount Partner ",
    "version": "14.0.1.1.0",
    "category": "Customer",
    "license": "AGPL-3",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["sale" , "base","sale_order_line_sequence","hdc_company_hydra"],
    "data": [
        "view/res_partner_view.xml",
        "security/ir.model.access.csv",
    ],
    "auto_install": False,
    "installable": True,
}

