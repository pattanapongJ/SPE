# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models, api
from odoo.osv import expression
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta, datetime

class WizardMRCreateMoModifyLine(models.TransientModel):
    _name = 'wizard.mr.create.mo.modify.line'
    _description = 'wizard mrp mr create mo modify line'

    wizard_mr_to_mo_ids = fields.Many2one(
        comodel_name="wizard.mr.create.mo.modify",
        string="mrp to create mo modify",
    )
    product_line_modify_id = fields.Many2one(
        comodel_name="mr.product.list.modify.line",
        string="product modify line",
    )
    selected = fields.Boolean(string='Select',)
    date_required = fields.Date(string="Request Date",default=datetime.now(), required=True)
    product_id = fields.Many2one('product.product', string='Product')
    demand_qty = fields.Float(string='Demand',digits=(16, 2))
    to_be_produce = fields.Float(string='To be Produce',digits=(16, 2))
    produce_qty = fields.Float(string='Produce',digits=(16, 2)) #On Hand
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure", required=True,domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    
class WizardMRCreateMoModify(models.TransientModel):
    _name = 'wizard.mr.create.mo.modify'
    _description = 'wizard mrp mr create mo modify'

    mr_id = fields.Many2one('mrp.mr', string='MR')
    user_id = fields.Many2one('res.users', string='Requested by', default=lambda self: self.env.user.id)
    partner_id = fields.Many2one('res.partner',related='mr_id.partner_id')
    request_type = fields.Many2one('request.type.mr',related='mr_id.request_type', string='Request Type')
    product_type = fields.Many2one('product.type.mr',related='mr_id.product_type', string='Product Type')
    picking_type_id = fields.Many2one('stock.picking.type', string='Factory', related='mr_id.picking_type_id',)
    scheduled_date = fields.Datetime(string="Scheduled Date", store=True, required=True,default=fields.Datetime.now,)
    delivery_date = fields.Date(string="Delivery Date" ,related='mr_id.delivery_date')
    order_line_ids = fields.One2many(comodel_name="wizard.mr.create.mo.modify.line", inverse_name='wizard_mr_to_mo_ids', string="Order Line",)
    selected = fields.Boolean(string="Select")

    @api.onchange('selected')
    def selected_change(self):
        for line in self.order_line_ids:
            if self.selected:
                line.selected = True
            else:
                line.selected = False

    def generate_mo(self):
        for product_line in self.order_line_ids:
            if product_line.selected:
                if product_line.product_line_modify_id.is_refurbish == False:
                    product = product_line.product_line_modify_id.product_id
                else:
                    product = product_line.product_line_modify_id.product_refurbish_id
                bom = self.env['mrp.bom'].sudo().search([('product_tmpl_id', '=', product.product_tmpl_id.id),('is_modify', '=', True)], limit=1)
                if bom:
                    production_vals = {
                        'product_id': product.id,
                        'bom_id': bom.id,
                        'product_qty': float(product_line.produce_qty),
                        'product_uom_id': product_line.uom_id.id,
                        'origin': self.mr_id.name,
                        'mr_id': self.mr_id.id,
                        'picking_type_id': self.picking_type_id.id,
                        'location_src_id': self.picking_type_id.default_location_src_id.id,
                        'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                        'date_planned_start': self.scheduled_date,
                        'product_line_modify_id': product_line.product_line_modify_id.id,
                    }
                    production = self.env['mrp.production'].sudo().create(production_vals)
                    production.reset_bom_id(product_line.produce_qty)
                    self.mr_id.state = 'in_progress'
                else:
                    production_vals = {
                        'product_id': product.id,
                        'product_qty': float(product_line.produce_qty),
                        'product_uom_id': product_line.uom_id.id,
                        'origin': self.mr_id.name,
                        'mr_id': self.mr_id.id,
                        'picking_type_id': self.picking_type_id.id,
                        'location_src_id': self.picking_type_id.default_location_src_id.id,
                        'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                        'date_planned_start': self.scheduled_date,
                        'product_line_modify_id': product_line.product_line_modify_id.id,
                    }
                    production = self.env['mrp.production'].sudo().create(production_vals)
                    self.mr_id.state = 'in_progress'

                
                move = self.env['stock.move'].create({
                    'raw_material_production_id': production.id,
                    'name': product_line.product_line_modify_id.name,
                    'product_id': product_line.product_line_modify_id.product_id.id,
                    'product_uom_qty': product_line.produce_qty,  
                    'product_uom': product_line.product_line_modify_id.product_uom.id,
                    'location_id': self.picking_type_id.default_location_src_id.id,
                    'location_dest_id': product_line.product_line_modify_id.product_id.with_company(production.company_id).property_stock_production.id,
                    'reference': self.mr_id.name,
                    'origin': self.mr_id.name,
                    'state': 'draft',
                })
                for part in product_line.product_line_modify_id.product_modify_detail_ids:
                    if part.type == 'add':
                        product_uom_qty = (product_line.produce_qty/product_line.demand_qty) * part.product_uom_qty
                        move = self.env['stock.move'].create({
                            'raw_material_production_id': production.id,
                            'name': part.name,
                            'product_id': part.product_id.id,
                            'product_uom_qty': product_uom_qty,  
                            'product_uom': part.product_uom.id,
                            'location_id': self.picking_type_id.default_location_src_id.id,
                            'location_dest_id': part.product_id.with_company(production.company_id).property_stock_production.id,
                            'reference': self.mr_id.name,
                            'origin': self.mr_id.name,
                            'state': 'draft',
                        })