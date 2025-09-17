# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError,ValidationError

class BlanketOrder(models.Model):
    _inherit = "sale.blanket.order"
    _description = "Blanket Order"

    ref_sale_id = fields.Many2one(
        "quotation.order",
        string="Reference Quotation",
        domain="[('state', 'in', ['approved','sale', 'done']), ('id', 'not in', ref_sale_ids)]",
        states={"draft": [("readonly", False)]},
        copy=False,
    )
    ref_sale_ids = fields.Many2many('quotation.order', compute='_compute_ref_sale_ids', store=False)

    @api.depends('ref_sale_id')
    def _compute_ref_sale_ids(self):
        for order in self:
            used_sale_ids = self.search([('ref_sale_id', '!=', False),('state','!=','expired')]).mapped('ref_sale_id').ids
            order.ref_sale_ids = [(6, 0, used_sale_ids)]

    @api.constrains('ref_sale_id')
    def _check_ref_sale_id(self):
        for order in self:
            if order.ref_sale_id:
                existing_order = self.search([
                    ('id', '!=', order.id),
                    ('ref_sale_id', '=', order.ref_sale_id.id),
                    ('state','!=','expired')
                ], limit=1)
                if existing_order:
                    raise ValidationError("The reference sale order has already been selected in another blanket order.")

    def _get_fields_to_copy_from_quotation(self):
        self.ensure_one()  # ป้องกันการใช้ในหลาย record

        return {
            'partner_id': self.ref_sale_id.partner_id,
            'partner_invoice_id': self.ref_sale_id.partner_invoice_id,
            'partner_shipping_id': self.ref_sale_id.partner_shipping_id,
            'po_date': self.ref_sale_id.po_date,
            'expire_date': self.ref_sale_id.expire_date,
            'customer_contact_date': self.ref_sale_id.customer_contact_date,
            'client_order_ref': self.ref_sale_id.client_order_ref,
            'project_name': self.ref_sale_id.project_name,
            'priority': self.ref_sale_id.priority,
            'warehouse_id': self.ref_sale_id.warehouse_id,
            'contact_person': self.ref_sale_id.contact_person,
            'validity_date': self.ref_sale_id.validity_date,
            'pricelist_id': self.ref_sale_id.pricelist_id,
            'sale_type_id': self.ref_sale_id.type_id,
            'modify_type_txt': self.ref_sale_id.modify_type_txt,
            'plan_home': self.ref_sale_id.plan_home,
            'payment_term_id': self.ref_sale_id.payment_term_id,
            'fiscal_position_id': self.ref_sale_id.fiscal_position_id,
            'days_delivery': self.ref_sale_id.days_delivery,
            'billing_route_id': self.ref_sale_id.billing_route_id,
            'billing_place_id': self.ref_sale_id.billing_place_id,
            'billing_terms_id': self.ref_sale_id.billing_terms_id,
            'payment_period_id': self.ref_sale_id.payment_period_id,
            'team_id': self.ref_sale_id.team_id,
            'user_id': self.ref_sale_id.user_id,
            'sale_spec': self.ref_sale_id.sale_spec,
            'sale_manager_id': self.ref_sale_id.sale_manager_id,
            'administrator': self.ref_sale_id.user_sale_agreement,
            'remark': self.ref_sale_id.remark,
            'requested_ship_date': self.ref_sale_id.requested_ship_date,
            'requested_receipt_date': self.ref_sale_id.requested_receipt_date,
            'global_discount': self.ref_sale_id.global_discount,
            'rounding_untax': self.ref_sale_id.rounding_untax,
            'rounding_taxes': self.ref_sale_id.rounding_taxes,
            'rounding_total': self.ref_sale_id.rounding_total,
            'outline_agreement': self.ref_sale_id.outline_agreement,
            'branch_id': self.ref_sale_id.branch_id,
            'tag_ids': self.ref_sale_id.tag_ids,
            'room': self.ref_sale_id.room,
            'incoterm_id': self.ref_sale_id.incoterm_id,

            'payment_method_id': self.ref_sale_id.payment_method_id,
            'billing_period_id': self.ref_sale_id.billing_period_id,
            'delivery_trl': self.ref_sale_id.delivery_trl,
            'delivery_trl_description': self.ref_sale_id.delivery_trl_description,
            'delivery_company': self.ref_sale_id.delivery_company,
            'delivery_company_description': self.ref_sale_id.delivery_company_description,
        }
    
    def _extend_line_vals(self, line):
        
        return {}
    
    # Example _extend_line_vals in other module
    # def _extend_line_vals(self, line):
    #     res = super()._extend_line_vals(line)
    #     res.update({
    #         'is_reward_line': line.is_reward_line,
    #         'free_product': line.free_product,
    #         'promotion_discount': line.promotion_discount,
    #     })
    #     return res
  
    def _copy_from_quotation(self):
        for rec in self:
            values_to_copy = rec._get_fields_to_copy_from_quotation()
            for field, value in values_to_copy.items():
                rec[field] = value

            new_lines = []
            for line in rec.ref_sale_id.quotation_line:
                if not line.is_global_discount:
                    new_line_vals = {
                        'product_id': line.product_id.id,
                        'original_uom_qty': line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'product_uom': line.product_uom.id,
                        'name': line.name,
                        'state': line.state,
                        'sequence': line.sequence,
                        'sequence2': line.sequence2,
                        'display_type': line.display_type,
                        'pick_location_id': line.pick_location_id.id if line.pick_location_id else False,
                        'warehouse_id': line.warehouse_id.id if line.warehouse_id else False,
                        'discount': line.discount,
                        'triple_discount': line.triple_discount,
                        'rounding_price': line.rounding_price,
                        'note': line.note,
                        'barcode': line.barcode,
                        'currency_id': line.currency_id.id if line.currency_id else False,
                        'company_id': line.company_id.id if line.company_id else False,
                        'is_global_discount': line.is_global_discount,
                    }
                    new_line_vals.update(self._extend_line_vals(line))
                    new_lines.append((0, 0, new_line_vals))
            rec.line_ids = new_lines

    @api.onchange('ref_sale_id')
    def _onchange_ref_sale_id(self):
        for rec in self:
            rec.line_ids = False
            if rec.ref_sale_id:
                rec._copy_from_quotation()

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
    #             # rec.finance_dimension_1_id = rec.ref_sale_id.finance_dimension_1_id
    #             # rec.finance_dimension_2_id = rec.ref_sale_id.finance_dimension_2_id
    #             # rec.finance_dimension_3_id = rec.ref_sale_id.finance_dimension_3_id
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
    #                             # 'finance_dimension_1_id':line.finance_dimension_1_id.id,
    #                             # 'finance_dimension_2_id':line.finance_dimension_2_id.id,
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