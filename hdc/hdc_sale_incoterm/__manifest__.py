# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2019 Victor M.M. Torres, Tecnativa SL
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "HDC Sale Incoterm",
    "version": "14.0.0.0.1",
    "category": "Sale",
    'summary': "Sale Incoterm",
    'description': "Sale Incoterm",
    "license": "AGPL-3",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["hdc_sale_addon","hdc_quotation_order","hdc_sale_agreement_addon","hdc_sale_agreement_finance_dimension"],
    "data": [
        "security/ir.model.access.csv",
        "view/partner_view.xml",
        "view/quotation_views.xml",
        "view/sale_blanket_order_views.xml",
        "view/sale_view.xml",
    ],
    "auto_install": False,
    "installable": True,
}

