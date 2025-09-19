# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2019 Victor M.M. Torres, Tecnativa SL
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "HDC Partner Field Addon",
    "version": "14.0.0.0.3",
    "category": "Contact",
    'summary': "HDC Partner Field Addon",
    'description': "HDC Partner Field Addon",
    "license": "AGPL-3",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["base","hdc_billing_period_route","account","hdc_partner_company_delivery","hdc_fiscal_position_by_company"],
    "data": [
        "view/partner_view.xml",
    ],
    "auto_install": False,
    "installable": True,
}

