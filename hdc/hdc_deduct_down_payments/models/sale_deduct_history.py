# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.tools import float_is_zero, float_compare
import datetime
from odoo.exceptions import UserError, AccessError
from itertools import groupby

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_down_line = fields.One2many(
        'sale.order.line', 
        'order_id', 
        string='Down Payment Lines', 
        compute='_compute_order_down_line', 
        store=False
    )

    @api.depends('order_line.is_downpayment')
    def _compute_order_down_line(self):
        for order in self:
            downpayment_lines = order.order_line.filtered(lambda line: line.is_downpayment)
            order.order_down_line = downpayment_lines

    def _get_invoiceable_deduct_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        down_payment_line_ids = []
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for line in self.order_line:
            if line.display_type == 'line_section':
                pending_section = line
                continue
            if line.qty_to_invoice == 0 or line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
                if line.is_downpayment and line.is_deduct_downpayment:
                    # Keep down payment lines separately, to put them together
                    # at the end of the invoice, in a specific dedicated section.
                    if len(line.invoice_lines) == 0:
                        down_payment_line_ids.append(line.id)
                    continue
                if pending_section:
                    invoiceable_line_ids.append(pending_section.id)
                    pending_section = None
                invoiceable_line_ids.append(line.id)

        return self.env['sale.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)


    def _create_invoices_deduct(self, grouped=False, final=False, date=None, deduct=[]):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        # 1) Create invoices.
        invoice_vals_list = []
        invoice_item_sequence = 1 # Incremental sequencing to keep the lines order on the invoice.
        for order in self:
            order = order.with_company(order.company_id)
            current_section_vals = None
            down_payments = order.env['sale.order.line']

            invoice_vals = order._prepare_invoice()
            invoiceable_lines = order._get_invoiceable_deduct_lines(final)
            if not any(not line.display_type for line in invoiceable_lines):
                continue

            invoice_line_vals = []
            down_payment_section_added = False

            for line in invoiceable_lines:
                
                product_bom = line.env['mrp.bom'].search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),('type', '=', 'normal')], limit=1)
                if not order.type_id.modern_trade and line.product_id.route_ids.filtered(lambda l: l.name == "Manufacture") and product_bom:
                    invoice_line_vals.append(
                        (0, 0, line._prepare_invoice_line(
                            sequence=invoice_item_sequence,
                        )),
                    )
                    invoice_item_sequence += 1
                    for line_bom in product_bom.bom_line_ids:
                        invoice_line_vals.append(
                            (0, 0, order._prepare_component_invoice_line(
                                line_bom,
                                sequence=invoice_item_sequence,
                                order_line=line
                            )),
                        )
                        invoice_item_sequence += 1
                else:
                    if not down_payment_section_added and line.is_downpayment:
                        # Create a dedicated section for the down payments
                        # (put at the end of the invoiceable_lines)
                        # deduct.update({"sequence":invoice_item_sequence})
                        # invoice_line_vals.append(
                        #     (0, 0, deduct),
                        # )
                        # invoice_item_sequence += 1
                        down_payment_section_added = True
                        invoice_line_vals.append(
                            (0, 0, line._prepare_deduct_invoice_line(
                                sequence=invoice_item_sequence,
                            )),
                        )
                        invoice_item_sequence += 1
                    else:
                        invoice_line_vals.append(
                            (0, 0, line._prepare_invoice_line(
                                sequence=invoice_item_sequence,
                            )),
                        )
                        invoice_item_sequence += 1
            
            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise self._nothing_to_invoice_error()
        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            invoice_vals_list = sorted(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys])
            for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['payment_reference'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.

        # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
        # in a single invoice. Example:
        # SO 1:
        # - Section A (sequence: 10)
        # - Product A (sequence: 11)
        # SO 2:
        # - Section B (sequence: 10)
        # - Product B (sequence: 11)
        #
        # If SO 1 & 2 are grouped in the same invoice, the result will be:
        # - Section A (sequence: 10)
        # - Section B (sequence: 10)
        # - Product A (sequence: 11)
        # - Product B (sequence: 11)
        #
        # Resequencing should be safe, however we resequence only if there are less invoices than
        # orders, meaning a grouping might have been done. This could also mean that only a part
        # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
        if len(invoice_vals_list) < len(self):
            SaleOrderLine = self.env['sale.order.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
                    sequence += 1

        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                subtype_id=self.env.ref('mail.mt_note').id
            )
        return moves



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    deposit_history_ids = fields.One2many(
        'sale.order.deposit.history',  # เชื่อมกับโมเดล sale.order.deposit.history
        'sale_order_line_id',  # ฟิลด์ที่ใช้ในการเชื่อม
        string='Deposit History',
    )
    remain_down_payment = fields.Float(compute='_compute_remain_down_payment', string='Remaining down payment amount',)
    is_deduct_downpayment = fields.Boolean(string="Is a deduct down payment", copy=False)

    @api.depends('deposit_history_ids')
    def _compute_remain_down_payment(self):
        for rec in self:
            initial_down_payment = rec.price_unit if rec.is_downpayment else 0.0
            total_deducted = sum(history.deducted_amount for history in rec.deposit_history_ids)
            rec.remain_down_payment = initial_down_payment - total_deducted

    def get_related_invoices(self):
        self.ensure_one()
        invoices = self.env['account.move'].search([
            ('invoice_lines.sale_line_ids', 'in', self.ids),
            ('move_type', '=', 'out_invoice')
        ])
        return invoices
    
    def _prepare_deduct_invoice_line(self, **optional_values):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        :param optional_values: any parameter that should be added to the returned invoice line
        """
        self.ensure_one()
        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': -1,
            'price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.tax_id.ids)],
            'analytic_account_id': self.order_id.analytic_account_id.id if not self.display_type else False,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'sale_line_ids': [(4, self.id)],
        }
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res


class SaleOrderDepositHistory(models.Model):
    _name = 'sale.order.deposit.history'
    _description = 'History of Deposits Deducted from Sales Order Lines'

    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line', required=True, ondelete='cascade')
    deposit_move_id = fields.Many2one('account.move', string='Deposit Invoice', required=True, ondelete='cascade')
    deduct_move_id = fields.Many2one('account.move', string='Deduct Invoice', required=True, ondelete='cascade')
    deducted_amount = fields.Monetary(string='Deducted Amount', required=True)
    currency_id = fields.Many2one(related='sale_order_line_id.currency_id', store=True)
    deduct_state = fields.Selection(related='deduct_move_id.state')
    
