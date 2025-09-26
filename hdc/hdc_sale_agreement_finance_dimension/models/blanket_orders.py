# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree
from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from collections import defaultdict
import re

class BlanketOrder(models.Model):
    _name = "sale.blanket.order"
    _inherit = ["sale.blanket.order","bs.base.finance.dimension"]

    @api.onchange('finance_dimension_1_id')
    def onchange_finance_dimension_1_id(self):
        self.line_ids.filtered(lambda x: not x.display_type).write({
            'finance_dimension_1_id': self.finance_dimension_1_id.id
        })

    @api.onchange('finance_dimension_2_id')
    def onchange_finance_dimension_2_id(self):
        self.line_ids.filtered(lambda x: not x.display_type).write({
            'finance_dimension_2_id': self.finance_dimension_2_id.id
        })

    @api.onchange('finance_dimension_3_id')
    def onchange_finance_dimension_3_id(self):
        self.line_ids.filtered(lambda x: not x.display_type).write({
            'finance_dimension_3_id': self.finance_dimension_3_id.id
        })

    def _get_fields_to_copy_from_quotation(self):
        self.ensure_one()
        values = super()._get_fields_to_copy_from_quotation()
        values.update({
            'finance_dimension_1_id': self.ref_sale_id.finance_dimension_1_id,
            'finance_dimension_2_id': self.ref_sale_id.finance_dimension_2_id,
            'finance_dimension_3_id': self.ref_sale_id.finance_dimension_3_id,
        })
        return values
    
    def _extend_line_vals(self, line):
        res = super()._extend_line_vals(line)
        res.update({
            'finance_dimension_1_id': line.finance_dimension_1_id.id,
            'finance_dimension_2_id': line.finance_dimension_2_id.id,
        })
        return res
    
    # @api.onchange('ref_sale_id')
    # def _onchange_ref_sale_id(self):
    #     for rec in self:
    #         rec.line_ids = False
    #         if rec.ref_sale_id:
    #             rec.partner_id = rec.ref_sale_id.partner_id
    #             rec.partner_invoice_id = rec.ref_sale_id.partner_invoice_id
    #             rec.partner_shipping_id = rec.ref_sale_id.partner_shipping_id
    #             rec.po_date = rec.ref_sale_id.po_date
    #             rec.expire_date = rec.ref_sale_id.expire_date
    #             rec.customer_contact_date = rec.ref_sale_id.customer_contact_date
    #             rec.client_order_ref = rec.ref_sale_id.client_order_ref
    #             rec.project_name = rec.ref_sale_id.project_name
    #             rec.priority = rec.ref_sale_id.priority
    #             rec.warehouse_id = rec.ref_sale_id.warehouse_id
    #             rec.contact_person = rec.ref_sale_id.contact_person
    #             rec.validity_date = rec.ref_sale_id.validity_date
    #             rec.pricelist_id = rec.ref_sale_id.pricelist_id
    #             rec.sale_type_id = rec.ref_sale_id.type_id
    #             rec.modify_type_txt = rec.ref_sale_id.modify_type_txt
    #             rec.plan_home = rec.ref_sale_id.plan_home
    #             rec.payment_term_id = rec.ref_sale_id.payment_term_id
    #             rec.fiscal_position_id = rec.ref_sale_id.fiscal_position_id
    #             rec.days_delivery = rec.ref_sale_id.days_delivery
    #             rec.payment_method_id = rec.ref_sale_id.payment_method_id
    #             rec.billing_period_id = rec.ref_sale_id.billing_period_id
    #             rec.billing_route_id = rec.ref_sale_id.billing_route_id
    #             rec.billing_place_id = rec.ref_sale_id.billing_place_id
    #             rec.billing_terms_id = rec.ref_sale_id.billing_terms_id
    #             rec.payment_period_id = rec.ref_sale_id.payment_period_id
    #             #Responsible
    #             rec.team_id = rec.ref_sale_id.team_id
    #             rec.user_id = rec.ref_sale_id.user_id
    #             rec.sale_spec = rec.ref_sale_id.sale_spec
    #             rec.sale_manager_id = rec.ref_sale_id.sale_manager_id
    #             rec.administrator = rec.ref_sale_id.user_sale_agreement
    #             rec.remark = rec.ref_sale_id.remark
    #             #Delivery
    #             rec.requested_ship_date = rec.ref_sale_id.requested_ship_date
    #             rec.requested_receipt_date = rec.ref_sale_id.requested_receipt_date
    #             rec.delivery_trl = rec.ref_sale_id.delivery_trl
    #             rec.delivery_trl_description = rec.ref_sale_id.delivery_trl_description
    #             rec.delivery_company = rec.ref_sale_id.delivery_company
    #             rec.delivery_company_description = rec.ref_sale_id.delivery_company_description
    #             #Finance Dimension
    #             rec.finance_dimension_1_id = rec.ref_sale_id.finance_dimension_1_id
    #             rec.finance_dimension_2_id = rec.ref_sale_id.finance_dimension_2_id
    #             rec.finance_dimension_3_id = rec.ref_sale_id.finance_dimension_3_id
    #             #Discount
    #             rec.global_discount = rec.ref_sale_id.global_discount
    #             rec.rounding_untax = rec.ref_sale_id.rounding_untax
    #             rec.rounding_taxes = rec.ref_sale_id.rounding_taxes
    #             rec.rounding_total = rec.ref_sale_id.rounding_total
    #             new_lines = []
    #             for line in rec.ref_sale_id.quotation_line:
    #                 if line.is_global_discount == False:
    #                     new_lines.append((0, 0, {
    #                             'product_id': line.product_id.id,
    #                             'original_uom_qty': line.product_uom_qty,
    #                             'price_unit': line.price_unit,
    #                             'product_uom': line.product_uom.id,
    #                             'name': line.name,
    #                             'state':line.state,
    #                             'sequence':line.sequence,
    #                             'sequence2':line.sequence2,
    #                             'display_type':line.display_type,
    #                             'pick_location_id':line.pick_location_id.id,
    #                             'warehouse_id':line.warehouse_id.id,
    #                             'finance_dimension_1_id':line.finance_dimension_1_id.id,
    #                             'finance_dimension_2_id':line.finance_dimension_2_id.id,
    #                             'discount':line.discount,
    #                             'triple_discount':line.triple_discount,
    #                             'rounding_price':line.rounding_price,
    #                             'note':line.note,
    #                             'barcode':line.barcode,
    #                             'currency_id':line.currency_id.id,
    #                             'company_id':line.company_id.id,
    #                             'is_global_discount':line.is_global_discount,
    #                         }))
    #             rec.line_ids = new_lines

class BlanketOrderLine(models.Model):
    _name = "sale.blanket.order.line"
    _inherit = ["sale.blanket.order.line","bs.base.finance.dimension"]
    
    @api.model
    def default_get(self, fields):
        rec = super(BlanketOrderLine, self).default_get(fields)
        if self.order_id:
            self.update({
                'finance_dimension_1_id': self.finance_dimension_1_id or self.order_id.finance_dimension_1_id.id,
                'finance_dimension_2_id': self.finance_dimension_2_id or self.order_id.finance_dimension_2_id.id,
                'finance_dimension_3_id': self.finance_dimension_3_id or self.order_id.finance_dimension_3_id.id
            })

        return rec
    
    

    