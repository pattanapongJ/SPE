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
#
###################################################################################
{
    "name": "HDC Purchase Addon Fields",
    "summary": "Purchase Addon Fields",
    "version": "14.0.0.0.1",
    "category": "Purchase Orders",
    'author': 'Hydra Data and Consulting Ltd',
    'website': 'http://www.hydradataandconsulting.co.th',
    "depends": ["purchase","purchase_request_report","partner_group","account","hdc_company_chain", "stock", "rma_ept","hdc_addon_product_fields"],
    "data": [
                'security/ir.model.access.csv',
                "views/purchase_request.xml",
                "views/purchase_views.xml",
                "views/purchase_agreement_view.xml",
                "views/account_incoterms_view.xml",
                "views/crm_claim_ept_view.xml"
            ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
