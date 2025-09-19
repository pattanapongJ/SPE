# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare

class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'
    _description = 'Backorder Confirmation'

    batch_id = fields.Many2one('stock.picking.batch', string='Batch Transfer')
    pickings_to_validate_ids = fields.Many2many('stock.picking', 'stock_picking_to_validate_rel')

    def process(self):
        pickings_to_do = self.env['stock.picking']
        pickings_not_to_do = self.env['stock.picking']
        for line in self.backorder_confirmation_line_ids:
            if line.to_backorder is True:
                pickings_to_do |= line.picking_id
            else:
                pickings_not_to_do |= line.picking_id

        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        pickings = self.env['stock.picking'].browse(self.env.context.get('button_validate_picking_ids'))
        if not pickings_to_validate:
            pickings_to_validate = []
            for pick_id in self.pickings_to_validate_ids:
                pickings_to_validate.append(pick_id.id)

            pickings = self.env['stock.picking'].browse(pickings_to_validate)

        if pickings_to_validate:
            pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate).with_context(skip_backorder=True)
            if pickings_not_to_do:
                self._check_less_quantities_than_expected(pickings_not_to_do)
                pickings_to_validate = pickings_to_validate.with_context(picking_ids_not_to_backorder=pickings_not_to_do.ids)
            if pickings.batch_id:
                res_button_validate = pickings_to_validate.button_validate()
            else:
                return pickings_to_validate.button_validate()
            
        if pickings.batch_id:
            batch_id = pickings.batch_id
            move_tranfer_ids = []
            domain = []   
            allowed_picking_states = ['waiting', 'confirmed', 'assigned']
            cancelled_batchs = self.env['stock.picking.batch'].search_read([('state', '=', 'cancel')], ['id'])
            cancelled_batch_ids = [batch['id'] for batch in cancelled_batchs]
            domain_states = list(allowed_picking_states)
            domain_states.append('draft')
            if batch_id.partner_id:
                domain += [('partner_id', '=', batch_id.partner_id.id)]
            if batch_id.picking_type_id:
                domain += [('picking_type_id', '=', batch_id.picking_type_id.id)]
            domain += [
                ('company_id', '=', batch_id.company_id.id),
                ('state', 'in', domain_states),
                '|',
                '|',
                ('batch_id', '=', False),
                ('batch_id', '=', batch_id.id),
                ('batch_id', 'in', cancelled_batch_ids),
                ]   

            for r in batch_id.move_tranfer_ids:
                base_domain = domain.copy()
                base_domain+= [('product_id','=',r.product_id.id),('origin', '=', r.origin)]
                allowed_move_line_tranfer_ids = self.env['stock.move'].search(base_domain)  
                for move_item in allowed_move_line_tranfer_ids:
                    move_tranfer_ids.append((4, move_item.id))

            vals = {
                        "partner_id": batch_id.partner_id.id,
                        "picking_type_id": batch_id.picking_type_id.id,
                        "company_id": batch_id.company_id.id,
                        "move_tranfer_ids":move_tranfer_ids,
                        "origin":batch_id.name
                    }
            res = self.env['stock.picking.batch'].create(vals)
        return True
    
    def process_stock_picking_only(self):
        pickings_to_do = self.env['stock.picking']
        pickings_not_to_do = self.env['stock.picking']
        for line in self.backorder_confirmation_line_ids:
            if line.to_backorder is True:
                pickings_to_do |= line.picking_id
            else:
                pickings_not_to_do |= line.picking_id

        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        if not pickings_to_validate:
            pickings_to_validate = []
            for pick_id in self.pickings_to_validate_ids:
                pickings_to_validate.append(pick_id.id)

        if pickings_to_validate:
            pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate).with_context(skip_backorder=True)
            if pickings_not_to_do:
                self._check_less_quantities_than_expected(pickings_not_to_do)
                pickings_to_validate = pickings_to_validate.with_context(picking_ids_not_to_backorder=pickings_not_to_do.ids)
            return pickings_to_validate.button_validate()
        return True
    
    def process_cancel_backorder(self):
        pickings = self.env['stock.picking'].browse(self.env.context.get('button_validate_picking_ids'))
        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        if not pickings_to_validate:
            pickings_to_validate = []
            for pick_id in self.pick_ids:
                pickings_to_validate.append(pick_id.id)

            pickings = self.env['stock.picking'].browse(pickings_to_validate)

        if pickings.batch_id:
            res = self.process_stock_picking_only()
            if self.env.context.get('pickings_to_detach'):
                self.env['stock.picking'].browse(self.env.context['pickings_to_detach']).batch_id = False
            return res
        else:
            res = super().process_cancel_backorder()
            return res



