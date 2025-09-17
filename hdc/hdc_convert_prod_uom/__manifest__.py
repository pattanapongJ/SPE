# -*- coding: utf-8 -*-
###################################################################################
#    Hydra Data and Consulting Ltd.
#    Copyright (C) 2019 Hydra Data and Consulting Ltd. (<http://www.hydradataandconsulting.co.th>).
#    Author: Hydra Data and Consulting Ltd. (<http://www.hydradataandconsulting.co.th>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
####################################################################################
{
    "name": "HDC Convert Product UOM",
    "version": "14.0.1",
    "category": "Sale",
    "author": "Hydra Data and Consulting Ltd",
    "website": "http://www.hydradataandconsulting.co.th",
    "description": """
            Master Convert Product UOM
    """,
    "depends": [
        "product",
        "sale",
        "hdc_product_kit",
        "hdc_master_key",
        "hdc_quotation_order",
        "hdc_sale_agreement_addon",
        "hdc_pricelist_update",
        "account"
    ],  # ใช้ hdc_product_kit เพราะ มีการทำงานทับ _action_launch_stock_rule อยากให้ทำของ hdc_convert_prod_uom ก่อน และ hdc_master_key ก็เป็น เคสเดียวกันกับ method _prepare_stock_moves
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "data/ir_actions_server.xml",
        "data/ir_actions_menu.xml",
        "view/product_template_view.xml",
        "view/product_template_list_view.xml",
        "view/update_uom_conversion.xml",
        "view/sale_view.xml",
        "view/purchase_view.xml",
        "view/quotation_view.xml",
        "view/sale_blanket_order_views.xml",
        "view/account_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
