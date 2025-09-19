# Copyright 2022 ForgeFlow S.L. (https://forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api,fields, models
from odoo.tools import float_compare, float_round, float_is_zero, OrderedSet
from itertools import groupby
from odoo.exceptions import AccessError, UserError, ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_component_invoice_line(self, component, sequence, order_line):
        self.ensure_one()
        # คำนวณจำนวนสินค้าของ component ที่จะออกใบแจ้งหนี้
        qty_to_invoice = order_line.product_uom._compute_quantity(component.product_qty * order_line.product_uom_qty, component.product_uom_id)
        res = {
            'display_type': False, 
            'is_component': True, 
            'sequence': sequence,
            'name': component.product_id.display_name or component.name,
            'product_id': component.product_id.id,
            'product_uom_id': component.product_uom_id.id,
            'quantity': qty_to_invoice,
            'price_subtotal': 0,  # สามารถปรับปรุงหากต้องการกำหนดราคาแบบรวมเอง
            'price_unit': 0,  # ปรับเป็นราคาต่อหน่วยถ้ามี
            # 'sale_line_ids': [(6, 0, [order_line.id])],  # ลิงก์กลับไปยัง sale order line
        }
        return res

    def _create_invoices_global_discount(self, grouped=False, final=False, date=None, global_discount_price=None):
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
                        (0, 0, order._prepare_down_payment_section_line(
                            sequence=invoice_item_sequence,
                        )),
                    )
                    down_payment_section_added = True
                    invoice_item_sequence += 1
                
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
                    if line.display_type == 'line_section':
                        section = line
                        current_section_vals = section._prepare_invoice_line(sequence=invoice_item_sequence)
                        invoice_line_vals.append((0, 0, current_section_vals))
                        invoice_item_sequence += 1
                    else:
                        item = line._prepare_invoice_line(sequence=invoice_item_sequence,)
                        if item['product_id'] == self.default_product_global_discount.id:
                            item['price_unit'] = global_discount_price * -1
                            item['quantity'] = 1
                            invoice_line_vals.append((0, 0, item),)
                        if line.product_id.is_master_key_service and item['product_id'] == line.product_id.id:
                            item['quantity'] = line.product_uom_qty
                        if item['quantity'] > 0 and item['product_id'] != self.default_product_global_discount.id:
                            invoice_line_vals.append((0, 0, item),)
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
        if global_discount_price:
            for invoice in invoice_vals_list:
                invoice['global_discount'] = str(global_discount_price)
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

        picking_ids = self.env['picking.lists.line'].search([
            ('sale_id', 'in', self.ids),
            ('state', '=', 'done'),
            '|',
            ('invoice_id', '=', False),
            ('invoice_id.state', '=', 'cancel'),
        ])

        if moves:
            latest_inv = moves.sorted(lambda m: m.id)[-1]
            picking_ids.write({'invoice_id': latest_inv.id})

        return moves
    

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_qty_delivered(self):
        res = super(SaleOrderLine, self)._compute_qty_delivered()
        for order_line in self:
            if order_line.qty_delivered_method == 'stock_move':
                boms = order_line.move_ids.filtered(lambda m: m.state != 'cancel').mapped('bom_line_id.bom_id')
                moves_m = order_line.move_ids.filtered(lambda m: m.state != 'cancel')
                boms_m = order_line.product_id.bom_ids.filtered(lambda b: b.type == 'normal')
                dropship_m = any(m._is_dropshipped() for m in moves_m)
                relevant_bom_m = boms_m.filtered(lambda b: b.type == 'normal' and
                        (b.product_id == order_line.product_id or
                        (b.product_tmpl_id == order_line.product_id.product_tmpl_id and not b.product_id)))
                dropship = any(m._is_dropshipped() for m in order_line.move_ids)
                if not boms and dropship:
                    boms = boms._bom_find(product=order_line.product_id, company_id=order_line.company_id.id, bom_type='phantom')
                relevant_bom = boms.filtered(lambda b: b.type == 'phantom' and
                        (b.product_id == order_line.product_id or
                        (b.product_tmpl_id == order_line.product_id.product_tmpl_id and not b.product_id)))
                # if relevant_bom_m:
                if not order_line.order_id.type_id.modern_trade and relevant_bom_m:
                    if dropship_m:
                        moves = order_line.move_ids.filtered(lambda m: m.state != 'cancel')
                        if any((m.location_dest_id.usage == 'customer' and m.state != 'done')
                               or (m.location_dest_id.usage != 'customer'
                               and m.state == 'done'
                               and float_compare(m.quantity_done,
                                                 sum(sub_m.product_uom._compute_quantity(sub_m.quantity_done, m.product_uom) for sub_m in m.returned_move_ids if sub_m.state == 'done'),
                                                 precision_rounding=m.product_uom.rounding) > 0)
                               for m in moves) or not moves:
                            order_line.qty_delivered = 0
                        else:
                            order_line.qty_delivered = order_line.product_uom_qty
                        continue
                    moves = order_line.move_ids.filtered(lambda m: m.state == 'done' and not m.scrapped)
                    filters = {
                        'incoming_moves': lambda m: m.location_dest_id.usage == 'customer' and (not m.origin_returned_move_id or (m.origin_returned_move_id and m.to_refund)),
                        'outgoing_moves': lambda m: m.location_dest_id.usage != 'customer' and m.to_refund
                    }
                    order_qty = order_line.product_uom._compute_quantity(order_line.product_uom_qty, relevant_bom_m.product_uom_id)
                    qty_delivered = moves._compute_manufactured_quantities(order_line.product_id, order_qty, relevant_bom_m, filters)
                    order_line.qty_delivered = relevant_bom_m.product_uom_id._compute_quantity(qty_delivered, order_line.product_uom)
                elif relevant_bom:
                    if dropship:
                        moves = order_line.move_ids.filtered(lambda m: m.state != 'cancel')
                        if any((m.location_dest_id.usage == 'customer' and m.state != 'done')
                               or (m.location_dest_id.usage != 'customer'
                               and m.state == 'done'
                               and float_compare(m.quantity_done,
                                                 sum(sub_m.product_uom._compute_quantity(sub_m.quantity_done, m.product_uom) for sub_m in m.returned_move_ids if sub_m.state == 'done'),
                                                 precision_rounding=m.product_uom.rounding) > 0)
                               for m in moves) or not moves:
                            order_line.qty_delivered = 0
                        else:
                            order_line.qty_delivered = order_line.product_uom_qty
                        continue
                    moves = order_line.move_ids.filtered(lambda m: m.state == 'done' and not m.scrapped)
                    filters = {
                        'incoming_moves': lambda m: m.location_dest_id.usage == 'customer' and (not m.origin_returned_move_id or (m.origin_returned_move_id and m.to_refund)),
                        'outgoing_moves': lambda m: m.location_dest_id.usage != 'customer' and m.to_refund
                    }
                    order_qty = order_line.product_uom._compute_quantity(order_line.product_uom_qty, relevant_bom.product_uom_id)
                    qty_delivered = moves._compute_kit_quantities(order_line.product_id, order_qty, relevant_bom, filters)
                    order_line.qty_delivered = relevant_bom.product_uom_id._compute_quantity(qty_delivered, order_line.product_uom)

                # If no relevant BOM is found, fall back on the all-or-nothing policy. This happens
                # when the product sold is made only of kits. In this case, the BOM of the stock moves
                # do not correspond to the product sold => no relevant BOM.
                elif boms:
                    # if the move is ingoing, the product **sold** has delivered qty 0
                    if all(m.state == 'done' and m.location_dest_id.usage == 'customer' for m in order_line.move_ids):
                        order_line.qty_delivered = order_line.product_uom_qty
                    else:
                        order_line.qty_delivered = 0.0
        return res

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            if line.state != 'sale' or not line.product_id.type in ('consu','product'):
                continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue

            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            addition = self.env["addition.operation.type"].search([("code", "=", "AO-02")], limit = 1)
            product_qty = line.product_uom_qty
            if line.order_id.type_id.is_borrow:
            # if addition:
            #     picking_type = self.env["stock.picking.type"].search([("addition_operation_types", "=", addition.id)])
            #     if picking_type:
                    # picking = self.env["stock.picking"].search([("sale_borrow", "=", line.order_id.id),("picking_type_id", "in", picking_type.ids)])
                    # move = self.env["stock.move"].search(
                    #     [("product_id", "=", line.product_id.id),
                    #      ("picking_id", "in", picking.ids), ("state", "!=", "cancel")])
                    # sum_qty = sum(move.mapped("product_uom_qty"))
                    total_delivered = 0
                    if line.borrow_qty > 0:
                        total_delivered = line.borrow_qty - line.return_qty
                        # if total_delivered >=0:
                        #     qty += total_delivered
                    # product_uom_qty = line.product_uom_qty - sum_qty + line.return_qty
                    product_uom_qty = line.product_uom_qty - total_delivered
                    if product_uom_qty < 0:
                        product_uom_qty = 0
                    product_qty = product_uom_qty
            else:
                product_qty = line.product_uom_qty - qty

            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
            product_bom = line.env['mrp.bom'].search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),('type', '=', 'normal')], limit=1)
            if not line.order_id.type_id.modern_trade and line.product_id.route_ids.filtered(lambda l: l.name == "Manufacture") and product_bom:
                for line_bom in product_bom.bom_line_ids:    
                    line_bom_uom = line_bom.product_uom_id
                    product_qty_bom = line_bom.product_qty * line.product_uom_qty
                    quant_uom_bom = line_bom.product_id.uom_id 
                    product_qty_bom, procurement_uom_bom = line_bom_uom._adjust_uom_quantities(product_qty_bom, quant_uom_bom)
                    procurements.append(self.env['procurement.group'].Procurement(
                        line_bom.product_id, product_qty_bom, procurement_uom_bom,
                        line.order_id.partner_shipping_id.property_stock_customer,
                        line_bom.product_id.display_name, line.order_id.name, line.order_id.company_id, values))
            else:
                procurements.append(self.env['procurement.group'].Procurement(
                    line.product_id, product_qty, procurement_uom,
                    line.order_id.partner_shipping_id.property_stock_customer,
                    line.product_id.display_name, line.order_id.name, line.order_id.company_id, values))

        if procurements:
            self.env['procurement.group'].run(procurements)
        return True
    
