# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models, api
from odoo.osv import expression
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta, datetime

class WizardMRPCreatePRLine(models.TransientModel):
    _name = 'wizard.mrp.create.pr.line'
    _description = 'order line'

    wizard_mrp_create_pr_ids = fields.Many2one(
        comodel_name="wizard.mrp.create.pr",
        string="mrp to create pr",
    )

    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Quantity', digits=(16, 2), required=True)
    estimated_cost = fields.Float(string='Estimated Cost', digits='Product Price', required=True)

    qty_available = fields.Float(string='Already Ordered', digits=(16, 2), compute='_compute_quantities')
    incoming_qty = fields.Float(string='Pending', digits=(16, 2), compute='_compute_quantities')

    @api.depends('product_id')
    def _compute_quantities(self):
        for line in self:
            warehouse = line.wizard_mrp_create_pr_ids.location_id.get_warehouse()

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

class WizardMRPCreatePR(models.TransientModel):
    _name = 'wizard.mrp.create.pr'
    _description = 'wizard mrp create pr'

    @api.model
    def _get_default_requested_by(self):
        return self.env["res.users"].browse(self.env.uid)

    mo_id = fields.Many2one('mrp.production', string='MO')
    request_type = fields.Many2one(
        comodel_name="purchase.request.type", required=True,string="PR Type"
    )
    requested_by = fields.Many2one(
        comodel_name="res.users",
        string="Requested by",
        required=True,
        copy=False,
        track_visibility="onchange",
        default=_get_default_requested_by,
        index=True,
    )
    currency_id = fields.Many2one('res.currency',required=True, string='Currency')
    order_line_ids = fields.One2many(
        comodel_name="wizard.mrp.create.pr.line",
        inverse_name='wizard_mrp_create_pr_ids',
        string="Order Line",
    )

    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Picking Type",
        required=True,
    )
    location_id = fields.Many2one('stock.location', string='Source Location')
    location_dest_id = fields.Many2one('stock.location', string='Source Location')

    def action_create_pr(self):
        return self.generate_pr()

    def generate_pr(self):
        if self.order_line_ids:
            order_line_ids = []
            for order_line in self.order_line_ids:
                name = order_line.product_id.name
                if order_line.product_id.code:
                    name = "[{}] {}".format(name, order_line.product_id.code)
                if order_line.product_id.description_purchase:
                    name += "\n" + order_line.product_id.description_purchase

                line = line = (0, 0, {
                    'product_id': order_line.product_id.id,
                    'name': name,
                    'estimated_cost': order_line.estimated_cost,
                    'product_qty': order_line.product_qty,
                    'product_uom_id': order_line.product_id.uom_id.id,
                })
                order_line_ids.append(line)
            
            purchase_request = self.env['purchase.request']
            purchase_request_id = purchase_request.create({
                'origin': self.mo_id.name,
                'request_type': self.request_type.id,
                'requested_by': self.requested_by.id,
                'currency_id': self.currency_id.id,
                'picking_type_id': self.picking_type_id.id,
                'is_create_pr': True,
                'line_ids': order_line_ids,
            }).id
            action = {
                'view_mode': 'form',
                'res_model': 'purchase.request',
                'type': 'ir.actions.act_window',
                'res_id': purchase_request_id,
                'target': 'self',
            }
            return action
        
    @api.onchange('request_type')
    def _onchange_request_type(self):
        self.picking_type_id = self.request_type.picking_type_id
        self.currency_id = self.request_type.currency_id