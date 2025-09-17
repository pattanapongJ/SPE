# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2019 Victor M.M. Torres, Tecnativa SL
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "HDC Company Addon Fiscal Position",
    "version": "14.0.0.0.1",
    "category": "Settings",
    'summary': "Company Addon Fiscal Position",
    'description': "Company Addon Fiscal Position",
    "license": "AGPL-3",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["base","account"],
    "data": [
        "security/ir.model.access.csv",
        "view/res_company_views.xml",
    ],
    "auto_install": False,
    "installable": True,
}

