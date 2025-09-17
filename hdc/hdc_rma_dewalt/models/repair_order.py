# Copyright 2022 ForgeFlow S.L. (https://forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _, fields, models,api
from odoo.exceptions import UserError, ValidationError
import re

class RepairOrder(models.Model):

    _inherit = "repair.order"

    sale_type = fields.Many2one(related="repair_type_id.sale_type")
    borrow_dewalt_ids = fields.Many2many("stock.picking","repair_order_borrow_picking_rel",  string="Borrow Dewalt")
    borrow_dewalt_count = fields.Integer(compute="_compute_borrow_dewalt_count")
    borrow_status = fields.Selection([('draft', 'Draft'),('done', 'Done')], string="Borrow Status", compute="_compute_borrow_status")
    
    @api.depends('borrow_dewalt_ids','borrow_dewalt_ids.state')
    def _compute_borrow_status(self):
        for rec in self:
            if len(rec.borrow_dewalt_ids) == 0:
                rec.borrow_status = 'done'
                continue
            if all(pick.state in ['cancel','done'] for pick in rec.borrow_dewalt_ids):
                rec.borrow_status = 'done'
            else:
                rec.borrow_status = 'draft'

    def _compute_borrow_dewalt_count(self):
        for rec in self:
            rec.borrow_dewalt_count = len(rec.borrow_dewalt_ids)

    def _compute_sale_order(self):
        for rec in self:
            rec.sale_order_ids = rec.mapped("operations.sale_line_id.order_id").ids
            rec.sale_order_count = len(rec.sale_order_ids)

    def _get_sale_order_data(self):
        self.ensure_one()
        res = super()._get_sale_order_data()
        res.update({
            "type_id": self.sale_type.id,
        })
        return res


    def action_create_sale_order(self):
        check_has_so = self.sale_order_ids.filtered(lambda l: l.state != 'cancel')
        if check_has_so:
            raise UserError(_('Cancel So Before Create new Sale Order Please'))
        order_model = self.env["sale.order"].sudo()
        order_line_model = self.env["sale.order.line"].sudo()
        orders = order_model.browse()
        for rec in self.filtered(
            lambda x:not x.sale_order_ids.filtered(lambda l: l.state != 'cancel') and x.create_sale_order
        ):  
            sequence = 1
            sale_order_data = rec._get_sale_order_data()
            sale_order = order_model.create(sale_order_data)
            # if rec.claim_id.rma_type == 'receive_modify':
            #     type_id = rec.env["sale.order.type"].search([('is_repair', '=', True)],limit=1)
            #     if type_id:
            #         sale_order.type_id = type_id
            if rec.partner_id.team_id:
                customer_credit_limit_id = rec.env["customer.credit.limit"].search([('partner_id','=',rec.partner_id.id)])
                if customer_credit_limit_id:
                    credit_line_id = rec.env["credit.limit.sale.line"].search([('credit_id','=',customer_credit_limit_id.credit_id.id),('sale_team_id','=',rec.partner_id.team_id.id)]) 
                    if credit_line_id:
                        sale_order.payment_method_id = credit_line_id.payment_method_id.id
                        sale_order.payment_term_id = credit_line_id.payment_term_id.id
                        sale_order.billing_period_id = credit_line_id.billing_period_id.id
            
            orders |= sale_order
            partner_shipping_id = False
            partner_invoice_id = False
            if sale_order.partner_shipping_id != sale_order.partner_id:
                partner_shipping_id = sale_order.partner_shipping_id
            if sale_order.partner_invoice_id != sale_order.partner_id:
                partner_invoice_id = sale_order.partner_invoice_id
            sale_order.onchange_partner_id()
            sale_order._onchange_sale_type()
            sale_order._onchange_pricelist_to_change_fiscal_position_id()
            if partner_shipping_id:
                sale_order.partner_shipping_id = partner_shipping_id
            if partner_invoice_id:
                sale_order.partner_invoice_id = partner_invoice_id
            # if rec.claim_id.rma_type == 'receive_modify' and not rec.claim_id.is_dewalt:
            product_descript_rma = {
                "display_type": "line_section",
                "name": rec.description_rma,
                "order_id": sale_order.id,
            }
            order_line_model.create(product_descript_rma)
            product_repair_rma = {
                "order_id": sale_order.id,
                "product_id": rec.product_id.id,
                "name": rec.description_rma if rec.description_rma else "-",
                "product_uom_qty": rec.product_qty,
                "price_unit": 0,
                "sequence": sequence,
                "sequence2": sequence,
            }
            sequence +=1
            sale_order_line = order_line_model.create(product_repair_rma)
            rec.operations.sale_line_id = sale_order_line.id
            if rec.claim_id.rma_type != 'receive_modify' or rec.claim_id.is_dewalt:
                for line in rec.operations:
                    sequence +=1
                    sale_order_line = order_line_model.create(
                        line._get_sale_line_data_sequence(sale_order,sequence)
                    )
                    line.sale_line_id = sale_order_line.id
            if rec.claim_id.rma_type == 'receive_modify' and rec.claim_id.is_dewalt:
                rec.auto_create_borrow_sale(sale_order)
            # sale_order._reset_sequence() #ถ้าลงsequence ถ้าไม่ลงก็ปิดไปซะ!!
        return self.action_show_sales_order(orders)
    
    def auto_create_borrow_sale(self, sale_order):
        """
        Automatically create a borrow picking (stock.picking) for the given sale order.
        """
        for repair_order in self:
            # ตรวจสอบ Picking Type
            picking_type = repair_order._get_picking_type()
            if not picking_type:
                raise ValidationError("Picking Type for borrowing is not defined.")
            
            # เตรียม Move Lines
            move_lines = repair_order._prepare_borrow_move_lines(picking_type)

            # เตรียมข้อมูลสำหรับการสร้าง Picking
            picking_data = repair_order._prepare_borrow_picking_data(sale_order, picking_type, move_lines)

            # สร้าง Picking
            picking = self.env['stock.picking'].create(picking_data)

            # # ยืนยัน Picking
            picking.action_confirm()
            picking.action_assign()  # จองสินค้า
            for line in picking.move_ids_without_package:
                line.qty_counted = line.product_uom_qty
            picking.action_confirm_warehouse()
            for line in picking.move_ids_without_package:
                for move_line in line.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty
            picking.button_validate()
            return picking

    def _get_picking_type(self):
        """
        Get the picking type for borrow operations.
        """
        return self.sale_type.picking_borrow_type_id

    def _prepare_borrow_move_lines(self, picking_type):
        """
        Prepare move lines for the borrow picking.
        """
        move_lines = []
        for operation in self.operations.filtered(lambda x: x.type == 'add' and x.product_id.type != "service"):
            move_lines.append((0, 0, {
                'product_id': operation.product_id.id,
                'name': operation.product_id.name or '',
                'product_uom_qty': operation.product_uom_qty,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'product_uom': operation.product_uom.id,
            }))
        return move_lines

    def _prepare_borrow_picking_data(self, sale_order=None, picking_type=None, move_lines=None):
        """
        Prepare the data dictionary for creating the borrow picking.
        """
        return {
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'origin': sale_order.name if sale_order else '',
            'sale_borrow': sale_order.id if sale_order else None,
            'partner_id': sale_order.partner_id.id if sale_order else None,
            'request_spare_parts_type': True,
            'type_borrow': 'not_return',
            'move_ids_without_package': move_lines,
        }
    
    @api.depends('operations.price_unit', 'operations.product_uom_qty', 'operations.product_id',
                 'fees_lines.price_unit', 'fees_lines.product_uom_qty', 'fees_lines.product_id',
                 'pricelist_id.currency_id', 'partner_id','operations.triple_discount')
    def _amount_tax(self):
        for order in self:
            val = 0.0
            currency = order.pricelist_id.currency_id or self.env.company.currency_id
            for operation in order.operations:
                total_dis = 0.0
                price_total = operation.price_unit * operation.product_uom_qty
                if operation.triple_discount:
                    try:
                        discounts = operation.triple_discount.replace(" ", "").split("+")
                        pattern = re.compile(r'^\d+(\.\d+)?%$|^\d+(\.\d+)?$')

                        for discount in discounts:
                            if not pattern.match(discount):
                                raise ValidationError(_('Invalid Discount format : 20%+100'))

                        for discount in discounts:
                            if discount.endswith("%"):
                                dis_percen = discount.replace("%", "")
                                total_percen = ((price_total) * float(dis_percen)) / 100
                                price_total -= total_percen
                                total_dis += total_percen
                            else:
                                total_baht = float(discount) 
                                price_total -= total_baht
                                total_dis += total_baht
                    except:
                        raise ValidationError(_('Invalid Discount format : 20%+100'))

                price = (operation.price_unit * operation.product_uom_qty) - total_dis 
                
                if operation.tax_id:
                    tax_calculate = operation.tax_id.compute_all(price, currency, 1, operation.product_id, order.partner_id)
                    for c in tax_calculate['taxes']:
                        val += c['amount']
            for fee in order.fees_lines:
                if fee.tax_id:
                    tax_calculate = fee.tax_id.compute_all(fee.price_unit, currency, fee.product_uom_qty, fee.product_id, order.partner_id)
                    for c in tax_calculate['taxes']:
                        val += c['amount']
            order.amount_tax = val

    def auto_create_borrow(self):
        """
        Automatically create a borrow picking (stock.picking) for the given sale order.
        """
        for repair_order in self:
            # ตรวจสอบ Picking Type
            picking_type = repair_order.repair_type_id.borrow_picking_type_id
            if not picking_type:
                raise ValidationError("Picking Type for borrowing is not defined.")
            # เตรียม Move Lines
            move_lines = repair_order._prepare_borrow_move_lines(picking_type)
            if not move_lines:
                # raise ValidationError("Move Lines for borrowing is not defined.")
                return False
            # เตรียมข้อมูลสำหรับการสร้าง Picking
            picking_data = repair_order._prepare_borrow_picking_data(picking_type=picking_type, move_lines=move_lines)
            # สร้าง Picking
            picking = self.env['stock.picking'].create(picking_data)
            # ยืนยัน Picking
            picking.action_confirm()
            picking.action_assign()  # 
            
            return picking

    def action_validate(self):
        
        claim = self.claim_id
        if claim:
            # if claim.rma_type == 'receive_modify' and claim.is_dewalt and claim.warranty_type != 'out':
            if claim.rma_type == 'receive_modify' and claim.is_dewalt:
                result = self.action_repair_confirm()
                picking = self.auto_create_borrow()
                if picking:
                    self.borrow_dewalt_ids |= picking
            else:
                result = super().action_validate()
        else:
            result = super().action_validate()
        return result

    def action_view_borrow_dewalt(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'name': 'Borrow Dewalt',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.borrow_dewalt_ids.ids)],
        }

class RepairLine(models.Model):
    _inherit = "repair.line"

    def _get_sale_line_data(self, sale_order):
        res = super(RepairLine, self)._get_sale_line_data(sale_order)
        res["triple_discount"] = self.triple_discount
        return res

    def _get_sale_line_data_sequence(self, sale_order, sequence):
        res = self._get_sale_line_data(sale_order)
        res.update({
            "sequence": sequence,
            "sequence2": sequence,
        })
        return res
    
    triple_discount = fields.Char('Discount')
    sale_line_id = fields.Many2one(
        comodel_name="sale.order.line", string="Sale line", copy=False
    )
    @api.depends('triple_discount', 'product_uom_qty', 'price_unit', 'tax_id')
    def _compute_price_subtotal(self):
        res = super(RepairLine, self)._compute_price_subtotal()
        for line in self:
            total_dis = 0.0
            price_total = line.price_unit * line.product_uom_qty
            if line.triple_discount:
                try:
                    discounts = line.triple_discount.replace(" ", "").split("+")
                    pattern = re.compile(r'^\d+(\.\d+)?%$|^\d+(\.\d+)?$')

                    for discount in discounts:
                        if not pattern.match(discount):
                            raise ValidationError(_('Invalid Discount format : 20%+100'))

                    for discount in discounts:
                        if discount.endswith("%"):
                            dis_percen = discount.replace("%", "")
                            total_percen = ((price_total) * float(dis_percen)) / 100
                            price_total -= total_percen
                            total_dis += total_percen
                        else:
                            total_baht = float(discount) 
                            price_total -= total_baht
                            total_dis += total_baht
                except:
                    raise ValidationError(_('Invalid Discount format : 20%+100'))

            price = (line.price_unit * line.product_uom_qty) - total_dis 
            taxes = line.tax_id.compute_all(price, line.repair_id.pricelist_id.currency_id, 1, line.product_id, line.repair_id.partner_id)
            
            line.update({
                # 'amount_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
                        
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])
        return res
