from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from itertools import groupby
from pytz import timezone, UTC
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang, format_amount

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    rl_history = fields.One2many('purchase.rl.history', 'purchase_id', string='RL History')
    check_done_picking = fields.Boolean(string='Check Done Picking', compute='_compute_check_done_picking', store=True)

    @api.depends("picking_ids", "picking_ids.state")
    def _compute_check_done_picking(self):
        for order in self:
            if order.picking_ids.filtered(lambda m: m.state not in ('skip_done', 'cancel')):
                if all(picking.state == 'done' for picking in order.picking_ids):
                    order.check_done_picking = True
                else:
                    order.check_done_picking = False
            else:
                order.check_done_picking = False

    def action_create_invoice_rl(self, order_line):
        """Create the invoice associated to the PO.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        sequence = 10
        for order in self:
            order = order.with_company(order.company_id)
            pending_section = None
            # Invoice values.
            invoice_vals = order._prepare_invoice()
            # Invoice line values (keep only necessary sections).
            receipt_list_id = self.env['receipt.list']
            ref_invoice = ""
            for line_rl in order_line:
                if line_rl._name == "gen.billing.rl.line":
                    receipt_list_id |= line_rl.receipt_list_line_id.receipt_list_id
                elif line_rl._name == "receipt.list.line" or line_rl._name == "receipt.list.line.service":
                    receipt_list_id |= line_rl.receipt_list_id
                
                line = line_rl.purchase_line_id
                if line.display_type == 'line_section':
                    pending_section = line
                    continue
                if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    if pending_section:
                        line_vals = pending_section._prepare_account_move_line_rl(move=False, line_rl=line_rl)
                        line_vals.update({'sequence': sequence})
                        invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                        sequence += 1
                        pending_section = None
                    line_vals = line._prepare_account_move_line_rl(move=False, line_rl=line_rl)
                    line_vals.update({'sequence': sequence})
                    invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                    sequence += 1
                else:
                    if line_rl.product_id.type == "service":
                        if pending_section:
                            line_vals = pending_section._prepare_account_move_line()
                            line_vals.update({'sequence': sequence})
                            invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                            sequence += 1
                            pending_section = None
                        line_vals = line._prepare_account_move_line()
                        line_vals.update({'sequence': sequence})
                        invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                        sequence += 1
            for rl in receipt_list_id:
                if rl.is_oversea:
                    # if rl.performa_invoice:
                    #     if ref_invoice != "":
                    #         ref_invoice += ", "
                    #     ref_invoice += rl.performa_invoice
                    if rl.commercial_invoice:
                        if ref_invoice != "":
                            ref_invoice += ", "
                        ref_invoice += rl.commercial_invoice
                else:
                    if rl.invoice_no:
                        if ref_invoice != "":
                            ref_invoice += ", "
                        ref_invoice += rl.invoice_no
            date_rl = min(receipt_list_id.mapped('receipted_date')) if receipt_list_id.mapped('receipted_date') else False
            if ref_invoice:
                invoice_vals["ref"] = ref_invoice
            if date_rl:
                invoice_vals["invoice_date"] = date_rl.date()
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
        return moves
    
    def action_create_vendor_bill_wizard(self):  
        context = {
            'default_purchase_id': self.id,
        }
        return {
                'type': 'ir.actions.act_window',
                'name': 'Create Bill',
                'res_model': 'purchases.advance.payment.inv',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }
    
    def _prepare_invoice(self):
        _invoice_value = super(PurchaseOrder, self)._prepare_invoice()
        _invoice_value.update({
            'shipper': self.shipper,
        })
        return _invoice_value
    
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    service_list_id = fields.One2many('receipt.list.line.service', 'purchase_line_id', string='Service List')

    def _prepare_account_move_line_rl(self, move=False, line_rl=None):
        self.ensure_one()
        aml_currency = move and move.currency_id or self.currency_id
        date = move and move.date or fields.Date.today()
        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': '%s: %s' % (self.order_id.name, self.name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'price_unit': self.currency_id._convert(self.price_unit, aml_currency, self.company_id, date, round=False),
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'analytic_account_id': self.account_analytic_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'purchase_line_id': self.id,
        }
        if line_rl._name == "gen.billing.rl.line":
            res.update({
                'quantity': line_rl.qty_to_invoice,
                'receipt_list_id': line_rl.receipt_list_line_id.id,
                'service_list_id': line_rl.service_list_id.id,
            })
        elif line_rl._name == "receipt.list.line":
            res.update({
                'quantity': line_rl.qty_to_invoice,
                'receipt_list_id': line_rl.id,
            })
        elif line_rl._name == "receipt.list.line.service":
            res.update({
                'quantity': line_rl.demand,
                'service_list_id': line_rl.id,
            })
        if not move:
            return res

        if self.currency_id == move.company_id.currency_id:
            currency = False
        else:
            currency = move.currency_id

        res.update({
            'move_id': move.id,
            'currency_id': currency and currency.id or False,
            'date_maturity': move.invoice_date_due,
            'partner_id': move.partner_id.id,
        })
        return res


class PurchaseOrderRL(models.Model):
    _name = "purchase.rl.history"
    _description = "RL History"

    purchase_id = fields.Many2one('purchase.order', string='Order Reference', required=True, ondelete='cascade', index=True, copy=False, readonly=True)
    receipt_list_id = fields.Many2one('receipt.list', string='Receipt List', index=True, ondelete="cascade", readonly=True)
    product_id = fields.Many2one('product.product', string='Product', required=True, readonly=True)
    receipt_no = fields.Char(string="Receipt No", readonly=True)
    po_no = fields.Char(string="PO No", readonly=True)
    before_price = fields.Float(string="Before Unit Price", readonly=True)
    price = fields.Float(string="Unit Price", readonly=True)