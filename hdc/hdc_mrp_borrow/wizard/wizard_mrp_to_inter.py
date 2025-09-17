# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models, api
from odoo.osv import expression
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta, datetime

class WizardMRPBorrowLine(models.TransientModel):
    _name = 'wizard.mrp.borrow.line'
    _description = 'order line'

    wizard_mrp_borrow_ids = fields.Many2one(
        comodel_name="wizard.mrp.borrow",
        string="mrp to inter transfer",
    )
    date_required = fields.Date(string="Request Date",default=datetime.now())
    product_id = fields.Many2one('product.product',domain=[('type', '=','product')], string='Product', required=True)
    location_id = fields.Many2one('stock.location', string='Source Location')
    # qty_available = fields.Float(related='product_id.qty_available', string='Already Ordered',digits=(16,2)) #On Hand
    # incoming_qty = fields.Float(related='product_id.incoming_qty', string='Pending',digits=(16,2)) #Pending Order
    need_to_order_qty = fields.Float( string='Demand', required=True, digits=(16,2))
    qty_available = fields.Float(string='Already Ordered', digits=(16, 2), compute='_compute_quantities')
    incoming_qty = fields.Float(string='Pending', digits=(16, 2), compute='_compute_quantities')
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.wizard_mrp_borrow_ids.location_id.id :
            self.location_id = self.wizard_mrp_borrow_ids.location_id.id

    @api.depends('product_id', 'location_id')
    def _compute_quantities(self):
        for line in self:
            warehouse = line.wizard_mrp_borrow_ids.location_id.get_warehouse()

            product_move_line = self.env['stock.quant'].search([
                ('product_id', '=', line.product_id.id),
                ('warehouse_id', '=', warehouse.id),
                ('location_id.usage', '=', 'internal'),

            ])
            
            product_move_in = self.env['stock.move'].search([
                ('product_id', '=', line.product_id.id),
                ('location_dest_id.warehouse_id', '=', warehouse.id),
                ('state', '=', "assigned"), 
                ('reference', '!=', False),
                ('picking_code', '=', "incoming"), 

            ])
            
            filtered_move_line = product_move_line.filtered(lambda q: q.product_id.type != 'service')
            filtered_move_in = product_move_in.filtered(lambda q: q.product_id.type != 'service')

            incoming_qty = sum(filtered_move_in.mapped('product_uom_qty'))
            qty_available_1 = sum(filtered_move_line.mapped('quantity'))

            line.qty_available = qty_available_1
            line.incoming_qty = incoming_qty
        


class WizardMRPBorrow(models.TransientModel):
    _name = 'wizard.mrp.borrow'
    _description = 'wizard mrp borrow'

    mo_id = fields.Many2one('mrp.production', string='MO')
    user_id = fields.Many2one('res.users', string='Requested by', required=True ,default=lambda self: self.env.user.id)
    request_date = fields.Date(string="Request Date", store=True, required=True ,default=datetime.now())
    order_line_ids = fields.One2many(
        comodel_name="wizard.mrp.borrow.line",
        inverse_name='wizard_mrp_borrow_ids',
        string="Order Line",
    )
    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Operation Type",
        required=True,
        domain=[('is_internal_borrow', '=',True),('code', '=','internal')]
    )
    location_dest_id = fields.Many2one("stock.location", string="Destination Location", required=True)
    location_id = fields.Many2one('stock.location', string='Source Location', required=True)
    is_request = fields.Boolean(string='Is Request',default=False)
    is_return = fields.Boolean(string='Is Return',default=False)

    @api.onchange('location_id')
    def _onchange_to_warehouse(self):
        for line in self.order_line_ids :
            line.location_id = self.location_id.id

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        if self.picking_type_id.default_location_dest_id.id:
            self.location_dest_id = self.picking_type_id.default_location_dest_id.id
        if self.picking_type_id.default_location_src_id.id:
            self.location_id = self.picking_type_id.default_location_src_id.id

    def _get_max_date_required(self):
        return max(self.order_line_ids.mapped('date_required'))

    @api.onchange('order_line_ids')
    def _onchange_order_line_ids(self):
        if self.order_line_ids:
            self.request_date = self._get_max_date_required()

    def action_generate_pr(self):
        if self.order_line_ids:
            none_purchase_qty = False
            for line_id in self.order_line_ids:
                if line_id.need_to_order_qty == 0:
                    none_purchase_qty = True
            if none_purchase_qty is False:
                return self.generate_pr()
            else:
                raise UserError(_("Demand QTY not found."))
        else:
            raise UserError(_("Detail product not found."))

    def generate_pr(self):
        if self.order_line_ids:
            order_line_ids = []
            for order_line in self.order_line_ids:
                if order_line.need_to_order_qty > 0:
                    line = line = (0, 0, {
                        'product_id': order_line.product_id.id,
                        'name': order_line.product_id.name,
                        'product_uom_qty': order_line.need_to_order_qty,
                        'date': order_line.date_required,
                        'location_id': order_line.location_id.id,
                        'product_uom': order_line.product_id.uom_id.id,
                        'location_dest_id': self.location_dest_id.id,
                    })
                    order_line_ids.append(line)
            stock = self.env['stock.picking']
            stock_id = stock.create({
                'origin': self.mo_id.name,
                'user_id': self.user_id.id,
                'scheduled_date': self.request_date,
                'move_ids_without_package': order_line_ids,
                'picking_type_id': self.picking_type_id.id,
                'location_dest_id': self.location_dest_id.id,
                'location_id': self.location_id.id,
            }).id
            action = {
                'view_mode': 'form',
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window',
                'res_id': stock_id,
                'target': 'self',
            }
            return action
        
    @api.onchange('is_request')
    def picking_type_id_domain_is_request(self):  
        picking_type_id_domain = [('is_internal_return', '=',True),('code', '=','internal')]
        if self.is_request:
            picking_type_id_domain = [('is_internal_borrow', '=',True),('code', '=','internal')] 
        return {"domain":{"picking_type_id":picking_type_id_domain}}
    
    @api.onchange('is_return')
    def picking_type_id_domain_is_return(self):  
        picking_type_id_domain = [('is_internal_borrow', '=',True),('code', '=','internal')]
        if self.is_return:
            picking_type_id_domain = [('is_internal_return', '=',True),('code', '=','internal')] 
        return {"domain":{"picking_type_id":picking_type_id_domain}}