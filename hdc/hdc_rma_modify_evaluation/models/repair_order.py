# Copyright 2022 ForgeFlow S.L. (https://forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _, fields,api, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime
from datetime import datetime, timedelta


class RepairOrder(models.Model):
    _inherit = "repair.order"

    description_rma = fields.Char(string="Description")
    origin_rma = fields.Many2one('crm.claim.ept', string="Source Document RMA")

    def _get_sale_order_data(self):
        self.ensure_one()
        warehouse_id = self.claim_id.picking_type_id.warehouse_id.id if self.claim_id else self.location_id.warehouse_id.id
        if not warehouse_id:
            sale_type = self.repair_type_id.sale_type
            if sale_type:
                if sale_type.warehouse_id:
                    warehouse_id = sale_type.warehouse_id.id
                else:
                    raise UserError(_("Please set Warehouse in Sale Type."))
            else:
                raise UserError(_("Please set Sale Type."))
        res = {
            "partner_id": self.partner_id.id,
            "partner_invoice_id": self.partner_invoice_id.id or self.partner_id.id,
            "warehouse_id": warehouse_id,
            "partner_shipping_id": self.address_id.id or self.partner_id.id,
            "origin": self.display_name,
            "note": self.quotation_notes,
            "pricelist_id": self.repair_type_id.sale_type.pricelist_id.id,
        }
        return res

    # def action_create_sale_order(self):
    #     order_model = self.env["sale.order"].sudo()
    #     order_line_model = self.env["sale.order.line"].sudo()
    #     orders = order_model.browse()
    #     for rec in self.filtered(
    #         lambda x: not x.sale_order_ids and x.create_sale_order
    #     ):
    #         sale_order_data = rec._get_sale_order_data()
    #         sale_order = order_model.create(sale_order_data)
        
    #         if self.claim_id.rma_type == 'receive_modify':
    #             type_id = self.env["sale.order.type"].search([('is_repair', '=', True)],limit=1)
    #             if type_id:
    #                 sale_order.type_id = type_id
    #         if self.partner_id.team_id:
    #             customer_credit_limit_id = self.env["customer.credit.limit"].search([('partner_id','=',self.partner_id.id)])
    #             if customer_credit_limit_id:
    #                 credit_line_id = self.env["credit.limit.sale.line"].search([('credit_id','=',customer_credit_limit_id.credit_id.id),('sale_team_id','=',self.partner_id.team_id.id)]) 
    #                 if credit_line_id:
    #                     sale_order.payment_method_id = credit_line_id.payment_method_id.id
    #                     sale_order.payment_term_id = credit_line_id.payment_term_id.id
    #                     sale_order.billing_period_id = credit_line_id.billing_period_id.id
            
    #         orders |= sale_order
    #         partner_shipping_id = False
    #         partner_invoice_id = False
    #         if sale_order.partner_shipping_id != sale_order.partner_id:
    #             partner_shipping_id = sale_order.partner_shipping_id
    #         if sale_order.partner_invoice_id != sale_order.partner_id:
    #             partner_invoice_id = sale_order.partner_invoice_id
    #         sale_order.onchange_partner_id()
    #         sale_order._onchange_sale_type()
    #         sale_order._onchange_pricelist_to_change_fiscal_position_id()
    #         if partner_shipping_id:
    #             sale_order.partner_shipping_id = partner_shipping_id
    #         if partner_invoice_id:
    #             sale_order.partner_invoice_id = partner_invoice_id
    #         product_descript_rma = {
    #             "display_type": "line_section",
    #             "name": rec.description_rma,
    #             "order_id": sale_order.id,
    #         }
    #         sale_order__line01 = order_line_model.create(product_descript_rma)
    #         product_repair_rma = {
    #             "order_id": sale_order.id,
    #             "product_id": rec.product_id.id,
    #             "name": rec.description_rma if rec.description_rma else "-",
    #             "product_uom_qty": rec.product_qty,
    #             "price_unit": 0,
    #         }
    #         sale_order_line = order_line_model.create(product_repair_rma)
    #         rec.operations.sale_line_id = sale_order_line.id
    #         if self.claim_id.rma_type != 'receive_modify':
    #             for line in rec.operations:
    #                 sale_order_line = order_line_model.create(
    #                     line._get_sale_line_data(sale_order)
    #                 )
    #                 line.sale_line_id = sale_order_line.id
    #         sale_order._reset_sequence() #ถ้าลงsequence ถ้าไม่ลงก็ปิดไปซะ!!
    #     return self.action_show_sales_order(orders)
    
    def _check_product_tracking(self):
        if self.repair_type_id.create_sale_order is True:
            return
        result = super(RepairOrder, self)._check_product_tracking()
        return result

