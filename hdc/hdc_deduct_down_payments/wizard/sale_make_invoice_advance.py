# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th)

import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _default_deduct_downpayment(self):
        if self._context.get('active_ids', []):
            sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
            move_ids = self.env['account.move']
            for order in sale_orders:
                # order = order.with_company(order.company_id)
                invoiceable_lines = order._get_invoiceable_lines(True)
                if invoiceable_lines.invoice_lines:
                    for line in invoiceable_lines.invoice_lines:
                        if line.move_id and line.move_id.deposit_balance > 0:
                            if line.move_id and any(sale_line.is_downpayment and not sale_line.is_deduct_downpayment for sale_line in line.sale_line_ids):
                                move_ids |= line.move_id
            return move_ids.ids
        else:
            return []
    
    def _domain_deduct_downpayment(self):
        move_ids = self._default_deduct_downpayment()
        return [('id', 'in', move_ids), ('state', '=', 'posted')]
    
    @api.onchange('deposit_no')
    def _onchange_deposit_no(self):
        for rec in self:
            res = {}
            res['domain'] = {'deposit_no': rec._domain_deduct_downpayment()}
            move_ids = rec._default_deduct_downpayment()
            if move_ids:
                rec.advance_payment_method = 'deduct'
                # ตั้งค่า default deposit_no เป็นรายการแรกที่เจอใน move_ids
                if not rec.deposit_no:
                    first_move = rec.env['account.move'].browse(move_ids[0])
                    rec.deposit_no = first_move
                # คำนวณ deduct_fixed_amount จากค่าสูงสุดของ SO แต่ไม่เกิน total_down_payment ที่เหลือ
                if rec.deposit_no and self._context.get('active_ids', []):
                    sale_orders = rec.env['sale.order'].browse(self._context.get('active_ids', []))
                    if sale_orders:
                        so_amount = sum(sale_orders.order_line.mapped('price_total'))
                        subtotal_delivery = 0
                        for delivery in sale_orders.order_line.filtered(lambda l: l.qty_delivered):
                            subtotal_delivery += delivery.qty_delivered * delivery.price_unit
                        remaining_deposit = rec.deposit_no.deposit_balance
                        rec.deduct_fixed_amount = min(so_amount, remaining_deposit, subtotal_delivery)
                
            return res
    @api.model
    def _default_product_deduct_id(self):
        product_id = self.env['ir.config_parameter'].sudo().get_param('hdc_deduct_down_payments.default_deduct_product_id')
        return self.env['product.product'].browse(int(product_id)).exists()
    
    advance_payment_method = fields.Selection(selection_add=[
        ('deduct', 'Deduct down payments')
    ], ondelete={'deduct': 'set default'})

    deposit_no = fields.Many2one('account.move', string='Deposit No', domain=_domain_deduct_downpayment)
    deduct_down_payments = fields.Boolean(string='Deduct down payments')
    deduct_percentage = fields.Float(string='Deduct (percentage)', default=0.0)
    deduct_fixed_amount = fields.Float(string='Deduct (fixed amount)', default=0.0)
    total_down_payment = fields.Monetary(string='Total Down payment', compute='_compute_down_payment_totals')
    balance_down_payment = fields.Monetary(string='Balance Down payment', compute='_compute_down_payment_totals')
    deduct_amount = fields.Monetary(string='Deduct', compute='_compute_deduct_amount')
    product_deduct_id = fields.Many2one('product.product', string='Down Payment Product', domain=[('type', '=', 'service')],
        default=_default_product_deduct_id)

    @api.onchange('advance_payment_method')
    def _onchange_clear_deduct_rec(self):
        if self.advance_payment_method != 'deduct':
            # self.deposit_no = False
            self.deduct_percentage = 0.0
            self.deduct_fixed_amount = 0.0

    @api.onchange('deposit_no', 'deduct_percentage', 'deduct_fixed_amount')
    def _onchange_deposit_deduction(self):
        if self.deposit_no:
            if self.deduct_percentage > 100:
                self.deduct_percentage = 100.0
            if self.deduct_fixed_amount > self.deposit_no.deposit_balance:
                self.deduct_fixed_amount = self.deposit_no.deposit_balance

    @api.depends('deposit_no', 'deduct_percentage', 'deduct_fixed_amount')
    def _compute_down_payment_totals(self):
        for record in self:
            if record.deposit_no:
                record.total_down_payment = record.deposit_no.deposit_balance
                record.balance_down_payment = record.deposit_no.deposit_balance - record.deduct_fixed_amount - (record.deposit_no.deposit_balance * (record.deduct_percentage / 100))
            else:
                record.total_down_payment = 0.0
                record.balance_down_payment = 0.0

    @api.depends('deduct_percentage', 'deduct_fixed_amount')
    def _compute_deduct_amount(self):
        for record in self:
            if record.deposit_no:
                record.deduct_amount = record.deduct_fixed_amount + (record.deposit_no.deposit_balance * (record.deduct_percentage / 100))
            else:
                record.deduct_amount = 0.0


    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        if self.advance_payment_method == 'deduct':
            if not self.product_deduct_id:
                vals = self._prepare_deposit_product()
                self.product_deduct_id = self.env['product.product'].create(vals)
                self.env['ir.config_parameter'].sudo().set_param('hdc_deduct_down_payments.default_deduct_product_id', self.product_deduct_id.id)
            order_lines = self.deposit_no.invoice_line_ids.mapped('sale_line_ids')
            sale_line_obj = self.env['sale.order.line']
            so_line_values = {
                'name': _('Deduct Down Payment: %s') % (time.strftime('%m %Y'),),
                'price_unit': self.deduct_amount,
                'product_uom_qty': 0,
                'order_id': sale_orders[0].id,
                'product_uom': self.product_deduct_id.uom_id.id,
                'product_id': self.product_deduct_id.id,
                'is_downpayment': True,
                'is_deduct_downpayment': True,
            }
            so_line = sale_line_obj.create(so_line_values)
            self._create_invoice_deduct(so_line)
            if self._context.get('open_invoices', False):
                return sale_orders.action_view_invoice()
            return {'type': 'ir.actions.act_window_close'}
        else:
            return super(SaleAdvancePaymentInv, self).create_invoices()
        
    def _create_invoice_deduct(self, so_line):
        if self.deposit_no and self.deduct_amount > 0:
            # ตรวจสอบว่าจำนวนเงินที่หักไม่เกินยอดคงเหลือในใบมัดจำ
            if self.deduct_amount > self.deposit_no.deposit_balance:
                raise UserError("Deduct amount cannot exceed the remaining deposit amount.")

            # เรียกฟังก์ชัน create_invoice_from_amount เพื่อสร้างใบแจ้งหนี้ด้วยยอดที่หัก
            sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
            order_lines = self.deposit_no.invoice_line_ids.mapped('sale_line_ids')
            if not order_lines:
                raise UserError("No sale order lines found for the selected deposit.")
            # deduct_data = {
            #     'name': _('Deduct Down Payment: %s') % (time.strftime('%m %Y'),),
            #     'price_unit': 0,
            #     'quantity': 0,
            #     'account_id': self.deposit_no.journal_id.default_account_id.id,  # บัญชีสำหรับมัดจำ
            #     'currency_id': self.currency_id.id,
            #     # 'product_uom': self.product_id.uom_id.id,
            #     # 'product_id': self.product_id.id,
            #     # 'sale_line_ids': [(6, 0, [order_line.id])],  # ลิงก์กลับไปยัง sale order line
            # }

            # invoices = sale_orders._create_invoices_deduct(False, deduct=deduct_data)
            invoices = sale_orders._create_invoices_deduct(False, deduct=False)
            # for invoice in invoices:
            #     # ลบบรรทัดที่เป็น Down Payment ออกจากใบแจ้งหนี้
            #     down_payment_lines = invoice.invoice_line_ids.filtered(lambda l: l.sale_line_ids.is_downpayment and not l.sale_line_ids.is_deduct_downpayment)
            #     down_payment_lines.unlink()
            # สร้างบันทึกประวัติการหักมัดจำ
            self.env['sale.order.deposit.history'].create({
                'sale_order_line_id': order_lines[0].id, 
                'deposit_move_id': self.deposit_no.id,  
                'deduct_move_id': invoices[0].id,  
                'deducted_amount': self.deduct_amount,  
            })

            # อัปเดตยอดคงเหลือของใบมัดจำ
            self.deposit_no._compute_deposit_balance()
        else:
            raise UserError("Please specify a valid deposit and deduction amount.")
        
    def _prepare_invoice_values(self, order, name, amount, so_line):
        res = super()._prepare_invoice_values(order, name, amount, so_line)
        if self.advance_payment_method not in ['deduct','delivered']:
            res['deposit_balance'] = amount
        return res
    
