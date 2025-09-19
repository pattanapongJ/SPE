# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2019 Victor M.M. Torres, Tecnativa SL
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "HDC Master Key",
    "version": "14.0.0.0.7",
    "category": "Sale",
    'summary': "Master Key",
    'description': "Master Key",
    "license": "AGPL-3",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ['base',"mrp","hdc_sale","stock","purchase","hdc_mrp_mr","purchase_requisition","purchase_order_type"],
    "data": [
        "security/ir.model.access.csv",
        "data/stock_data.xml",
        "data/report_paperformat_data.xml",
        "reports/master_key_report.xml",
        "reports/master_key_report_views.xml",
        "wizard/wizard_purchase_mtk_view.xml",
        "wizard/wizard_create_purchase_mtk_view.xml",
        "view/mrp_view.xml",
        "view/product_views.xml",
        "view/sale_view.xml",
        "view/stock_view.xml",
        "view/purchase_views.xml",
        "view/res_partner_view.xml",
    ],
    "auto_install": False,
    "installable": True,
}

