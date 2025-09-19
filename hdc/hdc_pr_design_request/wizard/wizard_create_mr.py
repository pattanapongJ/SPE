# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models, api
from odoo.osv import expression

class WizardPDRNewProductConfirm(models.TransientModel):
    _name = 'wizard.pdr.new.product.confirm'
    _description = 'Wizard New Product confirm'

    pdr_id = fields.Many2one('mrp.pdr', string='PDR ID')

    def create_new_product(self):
        self.pdr_id.action_create_product()

class WizardPDRCreateMR(models.TransientModel):
    _name = 'wizard.pdr.create.mr'
    _description = 'Wizard Create MR'

    # location_src_id = fields.Many2one('stock.location', string='Factory', required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        tracking=True,)
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Factory',
        domain="[('code', '=', 'mrp_operation'), ('company_id', '=', company_id)]",required=True,)
    # picking_type_inter_id = fields.Many2one(
    #     'stock.picking.type', 'Delivery',
    #     domain="[('code', 'in', ['outgoing','outgoing']), ('company_id', '=', company_id)]",required=True,)
    # location_dest_id = fields.Many2one('stock.location', domain=[("usage","=","internal")] ,string='Delivery')

    remark = fields.Text(string="Remark")
    pdr_id = fields.Many2one('mrp.pdr', string='PDR ID')


    def generate_new_mr(self):
        move_raw_ids = []
        for product_line in self.pdr_id.product_line_ids:
            move_raw_ids.append((0, 0, {
                'product_id': product_line.product_id.id,
                'uom_id': product_line.uom_id.id,
                'demand_qty': product_line.demand_qty,
                'factory_price': product_line.factory_price
            }))
        
        self.env['mrp.mr'].create({
            'request_type': self.pdr_id.request_type.id,
            'partner_id': self.pdr_id.partner_id.id,
            'product_type': self.pdr_id.product_type.id,
            'picking_type_id': self.picking_type_id.id,
            # 'location_dest_id': self.picking_type_inter_id.default_location_src_id.id,
            'department_id': self.pdr_id.department_id.id,
            'pdr_id': self.pdr_id.id,
            'product_line_ids': move_raw_ids,
            'remark': self.remark,
        })
        self.pdr_id.state= "done"