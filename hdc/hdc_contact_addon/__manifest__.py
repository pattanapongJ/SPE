# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2019 Victor M.M. Torres, Tecnativa SL
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "HDC Contact Addon",
    "version": "14.0.0.0.2",
    "category": "Contact",
    'summary': "Contact Addon",
    'description': "Contact Addon",
    "license": "AGPL-3",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["delivery","hr","base","hdc_purchase_addon_fields","hdc_certificate","hdc_purchase_request_addon","is_customer_is_vendor","branch"],
    "data": [
        "security/ir.model.access.csv",
        "security/res_group.xml",
        "view/partner_view.xml",
        "view/product_template_view.xml",
    ],
    "auto_install": False,
    "installable": True,
}

