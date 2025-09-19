# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models, api
from odoo.osv import expression
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta, datetime

class WizardMRPMRInterTransferFactoryLine(models.TransientModel):
    _name = 'wizard.mrp.mr.intertransfer.factory.line'
    _description = 'wizard mrp mr inter transfer factory line'

    wizard_mrp_to_int_fac_ids = fields.Many2one(
        comodel_name="wizard.mrp.mr.intertransfer.factory",
        string="mrp to inter transfer factory",
    )
    # select_product = fields.Boolean(string='select_product',)
    date_required = fields.Date(string="Request Date",default=datetime.now(), required=True)
    product_id = fields.Many2one('product.product', string='Product')
    location_id = fields.Many2one('stock.location', string='Source Location',)
    name = fields.Char(related='product_id.name', string="Product")
    qty_consume = fields.Float( string='To Consume',digits='Product Unit of Measure')
    qty_available = fields.Float(related='product_id.qty_available', string='Already Ordered',digits='Product Unit of Measure') #On Hand
    # shipping_qty = fields.Float(related='product_id.shipping_qty', string='Shipped',digits='Product Unit of Measure') #on the way
    incoming_qty = fields.Float(related='product_id.incoming_qty', string='Pending',digits='Product Unit of Measure') #Pending Order
    need_to_order_qty = fields.Float( string='Order Transfer', required=True, digits='Product Unit of Measure')
    product_uom = fields.Many2one('uom.uom', 'UoM',required=True, domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')

class WizardMRPMRInterTransferFactory(models.TransientModel):
    _name = 'wizard.mrp.mr.intertransfer.factory'
    _description = 'wizard mrp mr inter transfer factory'

    mr_id = fields.Many2one('mrp.mr', string='MO')
    user_id = fields.Many2one('res.users', string='Requested by', required=True ,default=lambda self: self.env.user.id)
    request_date = fields.Date(string="Request Date", store=True, required=True)
    order_line_ids = fields.One2many(
        comodel_name="wizard.mrp.mr.intertransfer.factory.line",
        inverse_name='wizard_mrp_to_int_fac_ids',
        string="Order Line",
    )
    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Operation Type",
        required=True,
        domain=[('addition_operation_types.code', '=','AO-06')]
    )
    to_warehouse = fields.Many2one("stock.warehouse", string = "From Warehouse", required=True)
    location_id = fields.Many2one("stock.location", string="Source Location", required=True)
    transit_location = fields.Many2one("stock.location", string="Transit Location", required=True)
    location_dest_id = fields.Many2one('stock.location', string='Destination Location', required=True)

    @api.onchange('to_warehouse')
    def _onchange_to_warehouse(self):
        self.location_id = self.to_warehouse.lot_stock_id.id

    @api.onchange('location_id')
    def _onchange_location_id(self):
        for line in self.order_line_ids:
            line.location_id = self.location_id.id

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        if self.picking_type_id.default_location_dest_id.id:
            self.transit_location = self.picking_type_id.default_location_dest_id.id
        if self.picking_type_id.default_location_src_id.id:
            self.location_dest_id = self.picking_type_id.default_location_src_id.id

    def _get_max_date_required(self):
        return max(self.order_line_ids.mapped('date_required'))

    @api.onchange('order_line_ids')
    def _onchange_order_line_ids(self):
        if self.order_line_ids:
            self.request_date = self._get_max_date_required()

    def action_generate_int(self):
        if self.order_line_ids:
            none_purchase_qty = False
            for line_id in self.order_line_ids:
                if line_id.need_to_order_qty == 0:
                    none_purchase_qty = True
            if none_purchase_qty is False:
                return self.generate_int()
            else:
                raise UserError(_("กรุณาตรวจสอบจำนวนโอนย้ายสินค้าอีกครั้ง ก่อนทำการโอนย้ายสินค้า"))
        else:
            raise UserError(_("Detail product not found."))

    def _get_picking_type(self):
        company_id = self.env.context.get('company_id') or self.env.company.id
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return picking_type[:1]

    def generate_int(self):
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
                        'location_dest_id': self.location_dest_id.id,
                        'product_uom': order_line.product_uom.id,
                    })
                    order_line_ids.append(line)
            stock = self.env['stock.picking']
            stock_id = stock.create({
                'origin': self.mr_id.name,
                'user_id': self.user_id.id,
                'scheduled_date': self.request_date,
                'move_ids_without_package': order_line_ids,
                'picking_type_id': self.picking_type_id.id,
                'to_warehouse': self.to_warehouse.id,
                'transit_location': self.location_id.id,
                'location_dest_id': self.transit_location.id,
                'location_id': self.location_dest_id.id,
                # 'company_id': self.env.context.get('company_id') or self.env.company.id
            }).id
            action = {
                'view_mode': 'form',
                'res_model': 'stock.picking',
                'type': 'ir.actions.act_window',
                'res_id': stock_id,
                'target': 'self',
            }
            return action
        