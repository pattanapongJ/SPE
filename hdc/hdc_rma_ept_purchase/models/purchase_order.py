# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _
from itertools import groupby
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError, UserError, ValidationError

class SaleOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_rma_count = fields.Integer('RMA Claims', compute='_compute_purchase_rma_count')

    def _compute_purchase_rma_count(self):
        """
        This method used to RMA count. It will display on the sale order screen.
        """
        for order in self:
            order.purchase_rma_count = self.env['purchase.crm.claim.ept'].search_count \
                ([('picking_id.purchase_id', '=', order.id)])

    def action_view_rma(self):
        """
        This action used to redirect from sale orders to RMA.
        """
        rma = self.env['purchase.crm.claim.ept'].search([('picking_id.purchase_id', '=', self.id)])
        if len(rma) == 1:
            claim_action = {
                'name':"RMA",
                'view_mode':'form',
                'res_model':'purchase.crm.claim.ept',
                'type':'ir.actions.act_window',
                'res_id':rma.id,
            }
        else:
            claim_action = {
                'name':"RMA",
                'view_mode':'tree,form',
                'res_model':'purchase.crm.claim.ept',
                'type':'ir.actions.act_window',
                'domain':[('id', 'in', rma.ids)]
            }
        return claim_action

    def action_create_invoice_rma_purchase(self, rma_id, product_claim):
        """Create the invoice associated to the PO.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        for order in self:
            if order.invoice_status != 'to invoice':
                continue

            order = order.with_company(order.company_id)
            pending_section = None
            # Invoice values.
            invoice_vals = order._prepare_invoice()
            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if product_claim:
                    for product_claim_id in product_claim:
                        if line.product_id.id == product_claim_id['product_id']:
                            if line.display_type == 'line_section':
                                pending_section = line
                                continue
                            if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                                if pending_section:
                                    invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_account_move_line()))
                                    pending_section = None
                                invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_account_move_line()))
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

        # 2) group by (company_id, partner_id, currency_id) for batch creation
        new_invoice_vals_list = []
        for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
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
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()
        rma = self.env['purchase.crm.claim.ept'].search([('id','=',rma_id)])
        rma.write({'refund_invoice_id': moves.id})
        return self.action_view_invoice(moves)

    def action_view_invoice(self, invoices=False):
        """This function returns an action that display existing vendor bills of
        given purchase order ids. When only one found, show the vendor bill
        immediately.
        """
        if not invoices:
            # Invoice_ids may be filtered depending on the user. To ensure we get all
            # invoices related to the purchase order, we read them in sudo to fill the
            # cache.
            self.sudo()._read(['invoice_ids'])
            invoices = self.invoice_ids

        result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        # choose the view_mode accordingly
        if len(invoices) > 1:
            result['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = invoices.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
