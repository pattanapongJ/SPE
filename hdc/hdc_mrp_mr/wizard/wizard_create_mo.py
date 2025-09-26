# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models, api
from odoo.osv import expression
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta, datetime

class WizardMRCreateMoLine(models.TransientModel):
    _name = 'wizard.mr.create.mo.line'
    _description = 'order line'

    wizard_mr_to_mo_ids = fields.Many2one(
        comodel_name="wizard.mr.create.mo",
        string="mrp to inter transfer",
    )
    # select_product = fields.Boolean(string='select_product',)
    date_required = fields.Date(string="Request Date",default=datetime.now(), required=True)
    product_id = fields.Many2one('product.product', string='Product')
    moq = fields.Float(related='product_id.moq_stock', string='MOQ')
    demand_qty = fields.Float(string='Demand',digits=(16, 2))
    to_be_produce = fields.Float(string='To be Produce',digits=(16, 2))
    produce_qty = fields.Float(string='Produce',digits=(16, 2)) #On Hand
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure", required=True,domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    
class WizardMRCreateMo(models.TransientModel):
    _name = 'wizard.mr.create.mo'
    _description = 'wizard mrp mr inter transfer'

    mr_id = fields.Many2one('mrp.mr', string='MR')
    user_id = fields.Many2one('res.users', string='Requested by', default=lambda self: self.env.user.id)
    partner_id = fields.Many2one('res.partner',related='mr_id.partner_id')
    request_type = fields.Many2one('request.type.mr',related='mr_id.request_type', string='Request Type')
    product_type = fields.Many2one('product.type.mr',related='mr_id.product_type', string='Product Type')
    picking_type_id = fields.Many2one('stock.picking.type', string='Factory', related='mr_id.picking_type_id',)
    scheduled_date = fields.Datetime(string="Scheduled Date", store=True, required=True,default=fields.Datetime.now,)
    delivery_date = fields.Date(string="Delivery Date" ,related='mr_id.delivery_date')
    order_line_ids = fields.One2many(comodel_name="wizard.mr.create.mo.line", inverse_name='wizard_mr_to_mo_ids', string="Order Line",)

    def generate_mr(self):
        for mr in self:
            if all(product_line.produce_qty != 0 and product_line.produce_qty <= (product_line.demand_qty-product_line.to_be_produce) for product_line in mr.order_line_ids) :
                for product_line in mr.order_line_ids:
                    bom = self.env['mrp.bom'].sudo().search([('product_tmpl_id', '=', product_line.product_id.product_tmpl_id.id),('type', '!=', 'phantom')], limit=1)
                    if bom:
                        production_vals = {
                            'product_id': product_line.product_id.id,
                            'bom_id': bom.id,
                            'product_qty': float(product_line.produce_qty),
                            'product_uom_id': product_line.uom_id.id,
                            'origin': mr.mr_id.name,
                            'mr_id': mr.mr_id.id,
                            'picking_type_id': mr.picking_type_id.id,
                            'location_src_id': mr.picking_type_id.default_location_src_id.id,
                            'location_dest_id': mr.picking_type_id.default_location_dest_id.id,
                            'date_planned_start': mr.scheduled_date,
                        }
                        production = self.env['mrp.production'].sudo().create(production_vals)
                        production.reset_bom_id(product_line.produce_qty)
                        mr.mr_id.state = 'in_progress'
                    else:
                        production_vals = {
                            'product_id': product_line.product_id.id,
                            'product_qty': float(product_line.produce_qty),
                            'product_uom_id': product_line.uom_id.id,
                            'origin': mr.mr_id.name,
                            'mr_id': mr.mr_id.id,
                            'picking_type_id': mr.picking_type_id.id,
                            'location_src_id': mr.picking_type_id.default_location_src_id.id,
                            'location_dest_id': mr.picking_type_id.default_location_dest_id.id,
                            'date_planned_start': mr.scheduled_date,
                        }
                        production = self.env['mrp.production'].sudo().create(production_vals)
                        mr.mr_id.state = 'in_progress'
            else:
                for product_line in mr.order_line_ids:
                    if product_line.produce_qty > (product_line.demand_qty-product_line.to_be_produce):
                        raise UserError(_("Please enter the correct Produce value."))
                raise UserError(_("Please enter the produce value as it cannot be zero."))