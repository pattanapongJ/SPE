# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2019 Victor M.M. Torres, Tecnativa SL
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "HDC Promotion Sale Agreement And Quotations",
    "version": "14.0.0.0.1",
    "category": "Sale",
    "license": "AGPL-3",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["hdc_promotion_priority","hdc_sale_exclude_taxes","hdc_sale_agreement_finance_dimension"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/sale_coupon_apply_code_views.xml",
        "views/sale_view.xml",
    ],
    "auto_install": False,
    "installable": True,
}

