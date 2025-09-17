# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero

class PurchasesAdvancePaymentInv(models.TransientModel):
    _name = "purchases.advance.payment.inv"
    _description = "Purchases Advance Payment Invoice"

    purchase_id = fields.Many2one(comodel_name="purchase.order")
    advance_payment_method = fields.Selection([
        ('receipt', 'Regular invoice'),
        ('percentage', 'Down payment (percentage)'),
        ('fixed', 'Down payment (fixed amount)'),
        ('receipt_list', 'Receipts List'),
        ], string='Create Vendor Bill', default='receipt', required=True,)
    
    receipt_list_ids = fields.Many2many('receipt.list', string='Receipt List')
    product_line_ids = fields.One2many('purchases.advance.payment.inv.rl.line', 'wiz_id')

    @api.onchange('advance_payment_method')
    def onchange_advance_payment_method(self):
        if self.advance_payment_method == "receipt_list":
            lines_product = self.env['receipt.list.line'].search([
                ('move_id.purchase_line_id.order_id', '=', self.purchase_id.id)
            ]).filtered(lambda l: l.qty_to_invoice > 0)

            lines_service = self.env['receipt.list.line.service'].search([
                ('purchase_line_id.order_id', '=', self.purchase_id.id),
                ('purchase_line_id.qty_to_invoice','>',0),
            ])

            receipt_lists = (lines_product.mapped('receipt_list_id') |
                            lines_service.mapped('receipt_list_id'))
            return {
                'domain': {
                    'receipt_list_ids': [('id', 'in', receipt_lists.ids)]
                }
            }

        return {'domain': {'receipt_list_ids': []}}
    
    @api.onchange('receipt_list_ids')
    def onchange_receipt_list_ids(self):
        self.product_line_ids = [(5, 0, 0)]

        lines_to_create = []

        for rl in self.receipt_list_ids:
            for line in rl.line_ids:
                if line.move_id.purchase_line_id.order_id.id == self.purchase_id.id:
                    if line.qty_to_invoice > 0 :
                        lines_to_create.append((0, 0, {
                        'receipt_list_line_id': line.id,
                        'purchase_line_id': line.move_id.purchase_line_id.id,
                        'product_id': line.product_id.id,
                        'categ_id': line.product_id.categ_id.id,
                        'receipt_list_id': rl.id,
                        'location_dest_id': line.location_dest_id.id,
                        'receipt_done': line.receipt_done,
                        'qty_to_bill_remain': line.qty_to_invoice,
                        'qty_to_bill': line.qty_to_invoice,
                        'product_uom': line.move_id.product_uom.id,
                    }))
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

            for line_svc in rl.line_service_ids:
                if line_svc.purchase_line_id.order_id.id == self.purchase_id.id:
                    if not float_is_zero(line_svc.purchase_line_id.qty_to_invoice, precision_digits=precision):
                        lines_to_create.append((0, 0, {
                            'receipt_list_line_service_id': line_svc.id,
                            'purchase_line_id': line_svc.purchase_line_id.id,
                            'product_id': line_svc.product_id.id,
                            'categ_id': line_svc.product_id.categ_id.id,
                            'receipt_list_id': rl.id,
                            'qty_to_bill_remain': line_svc.purchase_line_id.qty_to_invoice,
                            'qty_to_bill': line_svc.purchase_line_id.qty_to_invoice,
                            'product_uom': line_svc.purchase_line_id.product_uom.id,
                        }))

        self.product_line_ids = lines_to_create

    def create_invoices(self):
        
        if self.advance_payment_method == 'receipt':
            self.purchase_id.action_create_invoice()
        elif self.advance_payment_method == 'receipt_list':
            sequence = 10
            invoice_vals_list = []
            invoice_vals = self.purchase_id._prepare_invoice()
            for line in self.product_line_ids:
                if line.qty_to_bill > line.qty_to_bill_remain:
                    raise UserError(_('QTY to Bill must be less than or equal to Remain QTY to Bill.'))
                
                line_vals = line.purchase_line_id._prepare_account_move_line()
                line_vals.update({'sequence': sequence})
                line_vals.update({'quantity': line.qty_to_bill})
                if line.receipt_list_line_id:
                    line_vals.update({'receipt_list_id': line.receipt_list_line_id.id})
                elif line.receipt_list_line_service_id:
                    line_vals.update({'service_list_id': line.receipt_list_line_service_id.id})

                invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                sequence += 1
            invoice_vals_list.append(invoice_vals)

            moves = self.env['account.move']
            AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
            for vals in invoice_vals_list:

                moves |= AccountMove.with_company(vals['company_id']).create(vals)

        if self._context.get('open_invoices', False):
            return self.purchase_id.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}

class PurchasesAdvancePaymentInvRLLine(models.TransientModel):
    _name = "purchases.advance.payment.inv.rl.line"

    wiz_id = fields.Many2one("purchases.advance.payment.inv")
    receipt_list_line_id = fields.Many2one('receipt.list.line', string='Receipt List Line')
    receipt_list_line_service_id = fields.Many2one('receipt.list.line.service', string='Receipt List Line Service')
    purchase_line_id = fields.Many2one('purchase.order.line', string='Purchase line', index=True, ondelete="cascade")
    product_id = fields.Many2one(comodel_name='product.product', string='Product')
    categ_id = fields.Many2one(related = 'product_id.categ_id', string = 'Product Category', readonly = True)
    receipt_list_id = fields.Many2one('receipt.list', string='Receipt List')
    location_dest_id = fields.Many2one('stock.location', string="Location")
    receipt_done = fields.Float(string="Receipt Done")
    qty_to_bill_remain = fields.Float(string="Remain QTY to Bill")
    qty_to_bill = fields.Float(string="QTY to Bill")
    product_uom = fields.Many2one(comodel_name="uom.uom", string="UOM", readonly=True)