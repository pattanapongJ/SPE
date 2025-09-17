# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import timedelta, datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    borrow_count = fields.Integer(string='Purchase Requests', compute='_compute_borrow_count')
    return_count = fields.Integer(string='Return Count', compute='_compute_return_count')
    
    @api.depends('state')
    def _compute_borrow_count(self):
        for rec in self:
            origin = rec.name  # Origin is the same as the name of the MO
            rec.borrow_count = self.env['stock.picking'].search_count([('origin', '=', origin),('picking_type_id.is_internal_borrow','=',True)])
    
    @api.depends('state')
    def _compute_return_count(self):
        for rec in self:
            origin = rec.name  # Origin is the same as the name of the MO
            rec.return_count = self.env['stock.picking'].search_count([('origin', '=', origin),('picking_type_id.is_internal_return','=',True)])

    hide_btn_wizard_inter = fields.Boolean(string="Check Transfer BTN",default=True)

    def action_open_wizard_mrp_borrow(self):
        picking_type_id = self.env["stock.picking.type"].search([("is_internal_borrow", "=", True),("code", "=", "internal"),("warehouse_id","=",self.picking_type_id.warehouse_id.id)], limit = 1)
        
        order_line_ids = []
        for line in self.move_raw_ids:
            order_line_ids.append((0, 0, {
                    'product_id': line.product_id.id,
                    'date_required':datetime.now(),
                    'need_to_order_qty':0,
                    }))
            
        context = {
            'default_mo_id': self.id,
            'default_is_request': True,
            'default_order_line_ids':order_line_ids,
        }
        if picking_type_id:
            context.update({
                'default_location_id': picking_type_id.default_location_src_id.id,
                'default_location_dest_id': picking_type_id.default_location_dest_id.id,
                'default_picking_type_id': picking_type_id.id,
            })
        return {
                'type': 'ir.actions.act_window',
                'name': 'Create Stock Request',
                'res_model': 'wizard.mrp.borrow',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }
    
    def action_open_wizard_mrp_return(self):
        picking_type_id = self.env["stock.picking.type"].search([("is_internal_return", "=", True),("code", "=", "internal"),("warehouse_id","=",self.picking_type_id.warehouse_id.id)], limit = 1)
        context = {
            'default_mo_id': self.id,
            'default_is_return': True,
        }
        if picking_type_id:
            context.update({
                'default_location_id': picking_type_id.default_location_src_id.id,
                'default_location_dest_id': picking_type_id.default_location_dest_id.id,
                'default_picking_type_id': picking_type_id.id,
            })
        return {
                'type': 'ir.actions.act_window',
                'name': 'Create Stock Return',
                'res_model': 'wizard.mrp.borrow',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }
    
    def open_internal_transfer_borrow(self):
        """ This function opens the Purchase Request with the same origin as
        the current MO.
        """
        self.ensure_one()
        origin = self.name  # Origin is the same as the name of the MO
        br_ids = self.env['stock.picking'].search([('origin', '=', origin),('picking_type_id.is_internal_borrow','=',True)])
        
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Borrow',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', br_ids.ids)],
            'context': self._context,
        }
        
        if len(br_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': br_ids.id,
            })
        return action
    
    def open_internal_transfer_return(self):
        self.ensure_one()
        origin = self.name  # Origin is the same as the name of the MO
        rt_ids = self.env['stock.picking'].search([('origin', '=', origin),('picking_type_id.is_internal_return','=',True)])
        
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Return',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', rt_ids.ids)],
            'context': self._context,
        }
        
        if len(rt_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': rt_ids.id,
            })
        return action
    
    def action_cancel(self):
        super(MrpProduction, self).action_cancel()
        for rec in self:
            origin = rec.name
            if origin :
                transfer_ids = rec.env['stock.picking'].search([('origin', '=', origin),('state','not in',['done'])])
                for transfer in transfer_ids:
                    transfer.state = 'cancel'
        