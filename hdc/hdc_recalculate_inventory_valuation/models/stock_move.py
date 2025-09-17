# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, OrderedSet

import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    new_date_cost = fields.Datetime(string="Date Cost",copy=False)
  
    def _prepare_common_svl_vals(self):
        """When a `stock.valuation.layer` is created from a `stock.move`, we can prepare a dict of
        common vals.

        :returns: the common values when creating a `stock.valuation.layer` from a `stock.move`
        :rtype: dict
        """
        self.ensure_one()
        return {
            'stock_move_id': self.id,
            'company_id': self.company_id.id,
            'product_id': self.product_id.id,
            'description': self.reference and '%s - %s' % (self.reference, self.product_id.name) or self.product_id.name,
            'new_date_cost': self.new_date_cost
        }

    def _create_in_svl(self, forced_quantity=None):
        """Create a `stock.valuation.layer` from `self`.

        :param forced_quantity: under some circumstances, the quantity to value is different
                                than the initial demand of the move (Default = None)
        """
        StockValuationLayer = self.env['stock.valuation.layer'].sudo()
        in_svl = None

        moves = self.with_company(self.company_id)
        count = len(moves)
        for index, move in enumerate(moves):
            print(f'_create_in_svl.move {index+1}/{count}', move)
            valued_quantity = move._compute_valued_quantity(forced_quantity)
            unit_cost = move._determine_unit_cost()

            # Create initial SVL
            svl_vals = move.product_id._prepare_in_svl_vals(valued_quantity, unit_cost)
            svl_vals.update(move._prepare_common_svl_vals())
            if forced_quantity:
                svl_vals['description'] = 'Correction of %s (modification of past move)' % (
                    move.picking_id.name or move.name
                )

            in_svl = StockValuationLayer.create([svl_vals])

            # Recompute cost allocations (FIFO or AVG)
            candidate = move._get_candidate_svls(in_svl)
            candidate_unit_cost = move.price_unit

            if candidate:
                candidate_unit_cost = move._revalue_candidates(candidate)

            # Update product cost
            move._update_product_standard_price(candidate_unit_cost)

        return in_svl

    # ----------------------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------------------

    def _compute_valued_quantity(self, forced_quantity=None):
        """Compute the total quantity for valuation."""
        if forced_quantity:
            return forced_quantity
        valued_lines = self._get_in_move_lines()
        return sum(line.product_uom_id._compute_quantity(
            line.qty_done, self.product_id.uom_id
        ) for line in valued_lines)

    def _determine_unit_cost(self):
        """Determine unit cost depending on cost method."""
        unit_cost = abs(self._get_price_unit())
        if self.product_id.cost_method == 'standard':
            return self.product_id.standard_price
        return unit_cost

    def _get_candidate_svls(self, new_in_svl):
        """Get all SVLs for this product & company (including newly created)."""
        candidate = self.env['stock.valuation.layer'].sudo().search([
            ('product_id', '=', self.product_id.id),
            ('company_id', '=', self.company_id.id),
        ], order='cal_date_cost')
        return candidate | new_in_svl

    def _revalue_candidates(self, candidate):
        """Revalue incoming and outgoing layers depending on cost method."""
        in_candidates = candidate.filtered(lambda l: l.picking_type_id.code == "incoming").sorted('cal_date_cost')
        out_candidates = candidate.filtered(lambda l: l.picking_type_id.code == "outgoing").sorted('cal_date_cost')

        # Ensure incoming layers have correct remaining_qty/remaining_value
        for in_line in in_candidates:
            if not in_line.stock_valuation_layer_id:
                ld_cost = sum(in_line.stock_valuation_layer_ids.mapped("value"))
                in_line.write({
                    'remaining_qty': in_line.quantity,
                    'remaining_value': in_line.value + ld_cost,
                })

        # Revalue outgoing moves
        if self.product_id.cost_method == 'fifo':
            return self._apply_fifo(in_candidates, out_candidates)
        else:
            return self._apply_average(candidate, in_candidates, out_candidates)

    def _apply_fifo(self, in_candidates, out_candidates):
        """Apply FIFO costing."""
        candidate_unit_cost = self.price_unit
        for out_line in out_candidates:
            remaining_out_qty = abs(out_line.quantity)
            total_value = total_qty = 0

            for in_line in in_candidates:
                if remaining_out_qty <= 0:
                    break
                if in_line.remaining_qty > 0:
                    deduct_qty = min(in_line.remaining_qty, remaining_out_qty)
                    unit_cost = in_line.remaining_value / in_line.remaining_qty
                    deducted_value = unit_cost * deduct_qty

                    total_value += deducted_value
                    total_qty += deduct_qty

                    in_line.write({
                        'remaining_qty': in_line.remaining_qty - deduct_qty,
                        'remaining_value': unit_cost * (in_line.remaining_qty - deduct_qty),
                    })
                    remaining_out_qty -= deduct_qty

            if total_qty > 0:
                candidate_unit_cost = total_value / total_qty
                out_line.write({
                    'unit_cost': candidate_unit_cost,
                    'value': candidate_unit_cost * out_line.quantity,
                })

        return candidate_unit_cost

    def _apply_average(self, candidate, in_candidates, out_candidates):
        """Apply Average costing."""
        candidate_unit_cost = self.price_unit
        for out_line in out_candidates:
            remaining_out_qty = abs(out_line.quantity)

            # Weighted average from prior IN layers
            filtered = candidate.filtered(
                lambda l: l.cal_date_cost < out_line.cal_date_cost and l.remaining_qty > 0
            )
            total_value = sum(l.remaining_value for l in filtered)
            total_qty = sum(l.remaining_qty for l in filtered)

            if total_qty > 0:
                weighted_avg = total_value / total_qty
                candidate_unit_cost = weighted_avg
                out_line.write({
                    'unit_cost': weighted_avg,
                    'value': weighted_avg * out_line.quantity,
                })

            # Deduct quantities
            for in_line in in_candidates:
                if remaining_out_qty <= 0:
                    break
                if in_line.remaining_qty > 0:
                    deduct_qty = min(in_line.remaining_qty, remaining_out_qty)
                    unit_cost = in_line.remaining_value / in_line.remaining_qty
                    deducted_value = unit_cost * deduct_qty

                    in_line.write({
                        'remaining_qty': in_line.remaining_qty - deduct_qty,
                        'remaining_value': unit_cost * (in_line.remaining_qty - deduct_qty),
                    })
                    remaining_out_qty -= deduct_qty

        return candidate_unit_cost

    def _update_product_standard_price(self, candidate_unit_cost):
        """Update product's standard_price depending on cost method."""
        if self.product_id.cost_method == 'average' and self.product_id.quantity_svl:
            new_std_price = self.product_id.value_svl / self.product_id.quantity_svl
            self.product_id.with_context(disable_auto_svl=True).sudo().write({
                'standard_price': new_std_price
            })

        elif self.product_id.cost_method == 'fifo':
            self.product_id.with_context(disable_auto_svl=True).sudo().write({
                'standard_price': candidate_unit_cost
            })

    def _create_out_svl(self, forced_quantity=None):
        """Create `stock.valuation.layer` from `self` in optimized way."""
        svl_vals_list = []
        product_moves = {}

        # 1️⃣ เตรียม svl_vals_list สำหรับทุก move
        count = len(self)
        for i, move in enumerate(self):
            print(f'_create_out_svl: {i+1}/{count} ', move)
            move = move.with_company(move.company_id)
            valued_move_lines = move._get_out_move_lines()
            valued_quantity = sum(
                line.product_uom_id._compute_quantity(line.qty_done, move.product_id.uom_id)
                for line in valued_move_lines
            )
            if float_is_zero(forced_quantity or valued_quantity, precision_rounding=move.product_id.uom_id.rounding):
                continue

            svl_vals = move.product_id._prepare_out_svl_vals(forced_quantity or valued_quantity, move.company_id, move)
            svl_vals.update(move._prepare_common_svl_vals())
            if forced_quantity:
                svl_vals['description'] = 'Correction of %s (modification of past move)' % (move.picking_id.name or move.name)
            svl_vals['description'] += svl_vals.pop('rounding_adjustment', '')

            svl_vals_list.append(svl_vals)
            product_moves.setdefault(move.product_id.id, []).append(move)

        if not svl_vals_list:
            return self.env['stock.valuation.layer']

        # 2️⃣ สร้าง SVL ทั้งหมดทีเดียว
        out_svl = self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

        # 3️⃣ ทำงานต่อ product ทีละ product
        for product_id, moves in product_moves.items():
            candidate = self.env['stock.valuation.layer'].sudo().search([
                ('product_id', '=', product_id),
                ('company_id', '=', moves[0].company_id.id),
            ], order='cal_date_cost') | out_svl.filtered(lambda l: l.product_id.id == product_id)

            in_candidate = candidate.filtered(lambda l: l.picking_type_id.code == "incoming").sorted('cal_date_cost')
            out_candidate = candidate.filtered(lambda l: l.picking_type_id.code == "outgoing").sorted('cal_date_cost')

            # 4️⃣ Update remaining_qty/remaining_value ของ in_candidate
            updates_in = []
            for in_line in in_candidate:
                if not in_line.stock_valuation_layer_id:
                    ld_cost = sum(in_line.stock_valuation_layer_ids.mapped("value"))
                    updates_in.append((in_line.id, {
                        'remaining_qty': in_line.quantity,
                        'remaining_value': in_line.value + ld_cost
                    }))
            for line_id, vals in updates_in:
                self.env['stock.valuation.layer'].sudo().browse(line_id).write(vals)

            # 5️⃣ Process outgoing lines
            for out_line in out_candidate:
                remaining_out_qty = abs(out_line.quantity)

                if moves[0].product_id.cost_method == 'fifo':
                    total_deducted_value = 0
                    total_deducted_qty = 0

                    for in_line in in_candidate:
                        if remaining_out_qty <= 0:
                            break
                        if in_line.remaining_qty > 0:
                            deduct_qty = min(in_line.remaining_qty, remaining_out_qty)
                            before_unit_cost = in_line.remaining_value / in_line.remaining_qty
                            deducted_value = before_unit_cost * deduct_qty
                            total_deducted_value += deducted_value
                            total_deducted_qty += deduct_qty
                            in_line.remaining_qty -= deduct_qty
                            in_line.remaining_value -= before_unit_cost * deduct_qty
                            remaining_out_qty -= deduct_qty

                    if total_deducted_qty > 0:
                        candidate_unit_cost = total_deducted_value / total_deducted_qty
                        out_line.write({
                            'unit_cost': candidate_unit_cost,
                            'value': candidate_unit_cost * out_line.quantity
                        })

                else:  # average
                    filtered_candidate = in_candidate.filtered(lambda l: l.cal_date_cost < out_line.cal_date_cost and l.remaining_qty > 0)
                    total_qty = sum(l.remaining_qty for l in filtered_candidate)
                    total_value = sum(l.remaining_value for l in filtered_candidate)
                    if total_qty > 0:
                        weighted_avg_cost = total_value / total_qty
                        out_line.write({
                            'unit_cost': weighted_avg_cost,
                            'value': weighted_avg_cost * out_line.quantity
                        })

                        # Deduct quantities
                        for in_line in in_candidate:
                            if remaining_out_qty <= 0:
                                break
                            if in_line.remaining_qty > 0:
                                deduct_qty = min(in_line.remaining_qty, remaining_out_qty)
                                before_unit_cost = in_line.remaining_value / in_line.remaining_qty
                                in_line.remaining_qty -= deduct_qty
                                in_line.remaining_value -= before_unit_cost * deduct_qty
                                remaining_out_qty -= deduct_qty

            # 6️⃣ Update standard_price สำหรับ average
            if moves[0].product_id.cost_method == 'average':
                product = moves[0].product_id.with_company(moves[0].company_id.id).with_context(disable_auto_svl=True)
                new_std_price = product.value_svl / product.quantity_svl if product.quantity_svl else 0
                product.sudo().write({'standard_price': new_std_price})

        return out_svl
    
    def recalculate_all_cost(self):
        for move in self:
            candidate = self.env['stock.valuation.layer'].sudo().search([
                        ('product_id', '=', move.product_id.id),
                        ('company_id', '=', move.env.company.id),
                    ], order='cal_date_cost')
            candidate = candidate # Include newly created SVL
            # candidate_unit_cost = move.price_unit
            if candidate:
                in_candidate = candidate.filtered(lambda l: l.picking_type_id.code == "incoming").sorted('cal_date_cost')
                out_candidate = candidate.filtered(lambda l: l.picking_type_id.code == "outgoing").sorted('cal_date_cost')
                
                for in_line in in_candidate:
                    if not in_line.stock_valuation_layer_id:
                        ld_cost = sum(in_line.stock_valuation_layer_ids.mapped("value"))
                        in_line.write({'remaining_qty': in_line.quantity,
                                    'remaining_value': in_line.value + ld_cost})
                
                for out_line in out_candidate:
                    remaining_out_qty = abs(out_line.quantity)
                    
                    if move.product_id.cost_method == 'fifo':
                        # FIFO: Use first available cost with weighted average calculation
                        total_deducted_value = 0
                        total_deducted_qty = 0
                        
                        for in_line in in_candidate:
                            if remaining_out_qty <= 0:
                                break
                            if in_line.remaining_qty > 0:
                                deduct_qty = min(in_line.remaining_qty, remaining_out_qty)
                                before_unit_cost = (in_line.remaining_value/in_line.remaining_qty)
                                deducted_value = before_unit_cost  * deduct_qty
                                
                                total_deducted_value += deducted_value
                                total_deducted_qty += deduct_qty
                                
                                in_line.write({'remaining_qty': in_line.remaining_qty - deduct_qty,
                                               'remaining_value': before_unit_cost * (in_line.remaining_qty - deduct_qty)})
                                remaining_out_qty -= deduct_qty
                        
                        if total_deducted_qty > 0:
                            candidate_unit_cost = total_deducted_value / total_deducted_qty
                            out_line.write({
                                'unit_cost': candidate_unit_cost,
                                'value': candidate_unit_cost * out_line.quantity
                            })
                        
                    else:
                        # Average: Calculate weighted average cost from all available inventory
                        filtered_candidate = candidate.filtered(lambda l: l.cal_date_cost < out_line.cal_date_cost and l.remaining_qty > 0)
                        total_value = sum(in_line.remaining_value for in_line in filtered_candidate)
                        total_qty = sum(in_line.remaining_qty for in_line in filtered_candidate)
                        total_deducted_value = 0
                        total_deducted_qty = 0

                        if total_qty > 0:
                            weighted_avg_cost = total_value / total_qty
                            out_line.write({
                                'unit_cost': weighted_avg_cost,
                                'value': weighted_avg_cost * out_line.quantity
                            })
                            
                            # Deduct quantities from in_candidate
                            for in_line in in_candidate:
                                if remaining_out_qty <= 0:
                                    break
                                if in_line.remaining_qty > 0:
                                    deduct_qty = min(in_line.remaining_qty, remaining_out_qty)
                                    before_unit_cost = (in_line.remaining_value/in_line.remaining_qty)
                                    deducted_value = before_unit_cost  * deduct_qty
                                    total_deducted_value += deducted_value
                                    total_deducted_qty += deduct_qty
                                    in_line.write({'remaining_qty': in_line.remaining_qty - deduct_qty,
                                                    'remaining_value': before_unit_cost * (in_line.remaining_qty - deduct_qty)})
                                    remaining_out_qty -= deduct_qty
                                    
                if move.product_id.cost_method == 'average':
                    new_std_price = move.product_id.value_svl / move.product_id.quantity_svl
                    move.product_id.with_company(move.company_id.id).with_context(disable_auto_svl=True).sudo().write({'standard_price': new_std_price})



