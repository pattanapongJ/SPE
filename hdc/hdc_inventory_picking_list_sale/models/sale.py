from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

import traceback

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    count_picking_list = fields.Integer(string='picking list count', compute='_compute_picking_list')

    def _compute_picking_list(self):
        for sale in self:
            picking_ids = self.env['picking.lists.line'].search([('sale_id', '=', sale.id)])
            list_picking = list(set(picking_ids.mapped('picking_lists')))
            sale.count_picking_list = len(list_picking)

    def action_create_picking_wizard(self):
        line_ids = []
        if self.picking_ids:
            for pick in self.picking_ids:
                pick.move_lines._compute_picking_done_qty()
                move_lines_ids = pick.move_lines.filtered(lambda l: l.state not in ('cancel', 'done') and l.picking_code == 'outgoing' and l.is_done_picking == False)
                for move in move_lines_ids:
                    order_line = self.env['sale.order.line'].search(
                                [('product_id', '=', move.product_id.id), ('order_id', '=', self.id)])
                    line_ids.append((0, 0, {
                        'name': move.product_id.name,
                        'sale_id': self.id,
                        'product_id': move.product_id.id,
                        'location_id': move.location_id.id,
                        'qty': move.product_uom_qty,
                        'picking_id': pick.id,
                        'uom_id': move.product_uom.id,
                        'move_id': move.id,
                        'order_line': order_line.id
                        })
                    )

        wizard = self.env["wizard.create.picking.list"].create({
            "warehouse_id": self.warehouse_id.id,
            "picking_type_id": self.warehouse_id.out_type_id.id,
            "scheduled_date": pick.scheduled_date,
            "location_id": self.warehouse_id.out_type_id.default_location_src_id.id,
            "line_ids": line_ids
            })

        return wizard

    def action_create_picking(self):
        line_ids = []
        if self.picking_ids:
            for pick in self.picking_ids: # stock.picking = Delivery
                pick.move_lines._compute_picking_done_qty()
                move_lines_ids = pick.move_lines.filtered(lambda l: l.state not in ('cancel', 'done') and l.picking_code == 'outgoing' and l.is_done_picking == False)
                for move in move_lines_ids:
                    # putaway_id = self.env['stock.putaway.rule'].search([('product_id', '=', move.product_id.id)], limit = 1)
                    # if putaway_id:
                    #     pick_location_id = putaway_id.location_out_id.id
                    # else:
                    if move.sale_line_id.product_id.id != move.product_id.id:
                        putaway_id = self.env['stock.putaway.rule'].search([('product_id', '=', move.product_id.id)], limit = 1)
                        if putaway_id:
                            pick_location_id = putaway_id.location_out_id.id
                        else:
                            if move.sale_line_id.pick_location_id:
                                pick_location_id = move.sale_line_id.pick_location_id.id
                            else:
                                pick_location_id = move.location_id.id
                    else:
                        if move.sale_line_id.pick_location_id:
                            pick_location_id = move.sale_line_id.pick_location_id.id
                        else:
                            pick_location_id = move.location_id.id
                    # picking_id_done = self.env['picking.lists.line'].search(
                    #         [('product_id', '=', move.product_id.id), ('sale_id', '=', move.sale_line_id.order_id.id),
                    #         ('picking_lists.state', '=', "done")])
                    picking_id_done = self.env['picking.lists.line'].search(
                            [('product_id', '=', move.product_id.id), ('sale_id', '=', move.sale_line_id.order_id.id),
                            ('state', '=', "done")]) # ปรับการทำงานในระดับ line ให้มา check state ที่ระดับ line แทน
                    # picking_id_draft = self.env['picking.lists.line'].search(
                    #         [('product_id', '=', move.product_id.id), ('sale_id', '=', move.sale_line_id.order_id.id),
                    #          ('picking_lists.state', '=', "draft")])
                    picking_id_draft = self.env['picking.lists.line'].search(
                            [('product_id', '=', move.product_id.id), ('sale_id', '=', move.sale_line_id.order_id.id),
                             ('state', '=', "draft")]) # ปรับการทำงานในระดับ line ให้มา check state ที่ระดับ line แทน
                    product_uom_qty = move.sale_line_id.product_uom_qty

                    product_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', move.sale_line_id.product_id.product_tmpl_id.id),('type', '=', 'normal')], limit=1)
                    if not self.type_id.modern_trade and move.sale_line_id.product_id.route_ids.filtered(lambda l: l.name == "Manufacture") and product_bom:
                        for line_bom in product_bom.bom_line_ids:
                            if move.product_id == line_bom.product_id:
                                product_uom_qty = line_bom.product_qty * move.sale_line_id.product_uom_qty
                    
                    if move.product_uom.id != move.sale_line_id.product_uom.id and move.product_id.id == move.sale_line_id.product_id.id:
                        product_qty_f, procurement_uom_f = move.sale_line_id.convert_uom_factor(
                            move.sale_line_id.product_id, product_uom_qty, move.sale_line_id.product_uom
                        )
                        product_uom_qty = product_qty_f

                    product_uom_qty = product_uom_qty - sum(picking_id_done.mapped('qty_done')) - sum(picking_id_draft.mapped('qty')) # product_uom_qty = Quantity of sale order line
                    cancel_qty = move.sale_line_id.cancel_qty
                    if move.product_uom.id != move.sale_line_id.product_uom.id and move.product_id.id == move.sale_line_id.product_id.id:
                        product_qty_f, procurement_uom_f = move.sale_line_id.convert_uom_factor(
                            move.sale_line_id.product_id, move.sale_line_id.cancel_qty, move.sale_line_id.product_uom
                        )
                        cancel_qty = product_qty_f
                    product_uom_qty = product_uom_qty - abs(cancel_qty) # เคส cancel by line
                    order_line = self.env['sale.order.line'].search(
                                [('product_id', '=', move.product_id.id), ('order_id', '=', self.id)])

                    line_ids.append((0, 0, {
                        'name': move.product_id.name,
                        'sale_id': self.id,
                        'product_id': move.product_id.id,
                        'location_id': move.location_id.id,
                        'pick_location_id': pick_location_id,
                        'qty': product_uom_qty,
                        'picking_id': pick.id,
                        'uom_id': move.product_uom.id,
                        'move_id': move.id,
                        'order_line': move.sale_line_id.id,
                        'modify_type_txt': move.sale_line_id.modify_type_txt,
                        'plan_home': move.sale_line_id.plan_home,
                        'room': move.sale_line_id.room,
                        'external_customer': move.sale_line_id.external_customer.id if move.sale_line_id.external_customer else False,
                        'external_item': move.sale_line_id.external_item,
                        'barcode_customer': move.sale_line_id.barcode_customer,
                        'barcode_modern_trade': move.sale_line_id.barcode_modern_trade,
                        'description_customer': move.sale_line_id.description_customer,
                        }))
        
        wizard = self.env["wizard.create.picking.list"].create({
            "warehouse_id": self.warehouse_id.id,
            "picking_type_id": self.warehouse_id.out_type_id.id,
            "project_name": self.project_name.id,
            "land": self.modify_type_txt,
            "home": self.plan_home,
            "room": self.room,
            "scheduled_date": pick.scheduled_date,
            "location_id": self.warehouse_id.out_type_id.default_location_src_id.id,
            "line_ids": line_ids
            })

        action = {
            'name': 'Create Picking',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.create.picking.list',
            'res_id': wizard.id,
            'view_mode': 'form',
            "target": "new",
            }
        return action

    def action_view_picking_list(self):
        picking_ids = self.env['picking.lists.line'].search([('sale_id', '=', self.id)])
        res_id = list(set(picking_ids.mapped('picking_lists').ids))
        if len(res_id) > 1:
            view_mode = "tree,form"
        else:
            view_mode = "form"
            res_id = res_id[0]
        action = {
            'name': 'Picking Lists', 'type': 'ir.actions.act_window', 'res_model': 'picking.lists', 'res_id': res_id,
            'view_mode': view_mode, "domain": [("id", "in", res_id)],
            }
        return action

    def _create_invoices_pickinglist(self, grouped=False, final=False, date=None, global_discount_price=None, picking_list_line=None, sale_id_val=False):
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
        invoice_item_sequence = 1  # Incremental sequencing to keep the lines order on the invoice.
        for order in self:
            order = order.with_company(order.company_id)
            current_section_vals = None
            down_payments = order.env['sale.order.line']

            invoice_vals = order._prepare_invoice()
            # invoice_vals['modify_type_txt'] = order.modify_type_txt
            # invoice_vals['plan_home'] = order.plan_home
            # invoice_vals['project_name'] = order.project_name.id
            # invoice_vals['customer_po'] = order.customer_po

            invoiceable_lines = order._get_invoiceable_lines(final)

            if not any(not line.display_type for line in invoiceable_lines):
                continue

            invoice_line_vals = []
            down_payment_section_added = False

            for line in invoiceable_lines:
                if not down_payment_section_added and line.is_downpayment:
                    # Create a dedicated section for the down payments
                    # (put at the end of the invoiceable_lines)
                    invoice_line_vals.append(
                        (0, 0, order._prepare_down_payment_section_line(sequence = invoice_item_sequence, )), )
                    down_payment_section_added = True
                    invoice_item_sequence += 1

                product_bom = line.env['mrp.bom'].search(
                    [('product_tmpl_id', '=', line.product_id.product_tmpl_id.id), ('type', '=', 'normal')], limit = 1)
                if not order.type_id.modern_trade and line.product_id.route_ids.filtered(
                        lambda l: l.name == "Manufacture") and product_bom:

                    invoice_line_vals.append((0, 0, line._prepare_invoice_line(sequence = invoice_item_sequence, )), )
                    invoice_item_sequence += 1
                    for line_bom in product_bom.bom_line_ids:
                        invoice_line_vals.append((0, 0, order._prepare_component_invoice_line(line_bom,
                            sequence = invoice_item_sequence, order_line = line)), )
                        invoice_item_sequence += 1
                else:
                    item = line._prepare_invoice_line(sequence = invoice_item_sequence)
                    item['quantity'] = 0
                    dis_check = 0

                    for pl_line in picking_list_line:
                        if pl_line.product_id.id == item['product_id'] and pl_line.sale_id.id == sale_id_val and pl_line.order_line.id == line.id:
                            if pl_line.picking_lists.is_urgent and pl_line.picking_lists.state != 'done':
                                item['quantity'] += pl_line.qty
                            else:
                                item['quantity'] += pl_line.qty_done
                            # item['modify_type_txt'] = line.modify_type_txt
                            # item['plan_home'] = line.plan_home
                            # item['room'] = line.room
                            # item['external_customer'] = line.external_customer.id if line.external_customer else False
                            # item['barcode_customer'] = line.barcode_customer
                            # item['barcode_modern_trade'] = line.barcode_modern_trade
                            # item['description_customer'] = line.description_customer

                        if item['product_id'] == self.default_product_global_discount.id:
                            if dis_check != 1:
                                item['price_unit'] = global_discount_price*-1
                                item['quantity'] = 1
                                invoice_line_vals.append((0, 0, item), )
                                dis_check = 1
                        # else:
                        #     item['quantity'] = 0

                    if item['quantity'] > 0 and item['product_id'] != self.default_product_global_discount.id:
                        invoice_line_vals.append((0, 0, item), )
                    invoice_item_sequence += 1
            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise self._nothing_to_invoice_error()
        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            invoice_vals_list = sorted(invoice_vals_list,
                                       key = lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys])
            for grouping_keys, invoices in groupby(invoice_vals_list,
                                                   key = lambda x: [x.get(grouping_key) for grouping_key in
                                                                    invoice_grouping_keys]):
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
                    'ref': ', '.join(refs)[:2000], 'invoice_origin': ', '.join(origins),
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
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new = sequence,
                                                                                   old = line[2]['sequence'])
                    sequence += 1
        if global_discount_price:
            for invoice in invoice_vals_list:
                invoice['global_discount'] = str(global_discount_price)
        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.

        moves = self.env['account.move'].sudo().with_context(default_move_type = 'out_invoice').create(
            invoice_vals_list)
        if moves:
            for line in picking_list_line:
                if line.sale_id.id == sale_id_val:
                    line.invoice_id = moves.id
            moves.picking_list = list(set(picking_list_line.mapped('picking_lists').ids))
            moves._onchange_journal_default_prefix()
        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view('mail.message_origin_link', values = {
                'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')
                }, subtype_id = self.env.ref('mail.mt_note').id)
        
        return moves

    def update_sale_line_pick_location_id(self):
        for rec in self:
            for line in rec.order_line:
                putaway_id = line.env['stock.putaway.rule'].search([('product_id', '=', line.product_id.id), ('company_id', '=', line.company_id.id), ('location_out_id.warehouse_id', '=', line.warehouse_id.id)], limit = 1)
                if putaway_id:
                    line.pick_location_id = putaway_id.location_out_id.id
                else:
                    if self.warehouse_id:
                        line.pick_location_id = line.warehouse_id.out_type_id.default_location_src_id.id

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    pick_location_id = fields.Many2one('stock.location', string = 'Location')
    #-----------------เพิ่มมาทำเคส cancel by line-------------------
    cancel_qty = fields.Float(string='Cancel Qty', digits='Product Unit of Measure',copy=False) 
    remain_demand_qty = fields.Float(string='Remain Qty', digits='Product Unit of Measure', compute='_compute_remain_demand_qty',store=True)

    @api.depends('cancel_qty','product_uom_qty')
    def _compute_remain_demand_qty(self):
        for line in self:
            line.remain_demand_qty = line.product_uom_qty - abs(line.cancel_qty)

    #-----------------เพิ่มมาทำเคส cancel by line-------------------
    @api.onchange('product_id')
    def _onchange_location_product_id(self):
        putaway_id = self.env['stock.putaway.rule'].search([('product_id', '=', self.product_id.id), ('company_id', '=', self.company_id.id), ('location_out_id.warehouse_id', '=', self.warehouse_id.id)], limit = 1)
        if putaway_id:
            self.pick_location_id = putaway_id.location_out_id.id
        else:
            if self.warehouse_id:
                self.pick_location_id = self.warehouse_id.out_type_id.default_location_src_id.id


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    advance_payment_method = fields.Selection(
        selection_add = [('delivered', 'Regular invoice'),
                         ('picking', 'Picking List'),
                         ('picking_urgent', 'Picking List (Urgent)')],
        ondelete = {
            'delivered': 'set default', 'picking': 'cascade',
            'picking_urgent': 'cascade'
            })

    picking_list = fields.Many2many('picking.lists', string = 'Picking List')
    list_line_ids = fields.Many2many('picking.lists.line', string = 'Product List')

    @api.onchange('picking_list')
    def onchange_picking_list(self):
        domain = []
        if self.picking_list:
            lines = self.picking_list.mapped("list_line_ids")
            lines = self.env['picking.lists.line'].browse(lines)
            lines = lines.sorted(lambda l: l.sequence2 or 0)
            self.list_line_ids = lines
            domain = [('id', 'in', lines.ids)]
        else:
            self.list_line_ids = False

        return {'domain': {'list_line_ids': domain}}


    @api.onchange('advance_payment_method')
    def onchange_advance_payment_method(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        if self.advance_payment_method == "picking":
            # picking_ids = self.env['picking.lists.line'].search(
            #     [('sale_id', '=', sale_orders.id), ('state', '=', "done"), ('picking_lists.invoice_check', '=', False)])
            picking_ids = self.env['picking.lists.line'].search(
                [('sale_id', '=', sale_orders.id), ('state', '=', "done"),'|',
                    ('invoice_id', '=', False),
                    ('invoice_id.state', '=', 'cancel')])

            list_picking = picking_ids.mapped('picking_lists').ids
        elif self.advance_payment_method == "picking_urgent":
            picking_ids = self.env['picking.lists.line'].search(
                [('picking_lists.is_urgent','=',True),('sale_id', '=', sale_orders.id), ('state', '!=', "cancel"),'|',
                    ('invoice_id', '=', False),
                    ('invoice_id.state', '=', 'cancel')])

            list_picking = picking_ids.mapped('picking_lists').ids
        else:
            # picking_ids = self.env['picking.lists.line'].search(
            #     [('sale_id', '=', sale_orders.id),('picking_lists.invoice_check', '=', False)])

            picking_ids = self.env['picking.lists.line'].search(
                [('sale_id', '=', sale_orders.id)])

            list_picking = picking_ids.mapped('picking_lists').filtered(lambda l: l.is_urgent == True).ids
        return {'domain': {'picking_list': [("id", "in", list_picking)]}}

    def create_invoices(self):
        if self.advance_payment_method in ("picking", "picking_urgent"):
            sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))

            sale_orders._create_invoices_pickinglist(final = self.deduct_down_payments,global_discount_price=self.global_discount_price
                                         ,picking_list_line = self.list_line_ids, sale_id_val=sale_orders.id)

            if self._context.get('open_invoices', False):
                return sale_orders.action_view_invoice()
            return {'type': 'ir.actions.act_window_close'}
        else:
            res = super(SaleAdvancePaymentInv, self).create_invoices()
            return res
