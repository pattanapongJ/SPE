# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models, api
from odoo.osv import expression
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta, datetime

class WizardMRPCreateRFQLine(models.TransientModel):
    _name = 'wizard.mrp.create.rfq.line'
    _description = 'order line'

    wizard_mrp_create_rfq_ids = fields.Many2one(
        comodel_name="wizard.mrp.create.rfq",
        string="mrp to create rfq",
    )
    # date_required = fields.Date(string="Request Date",default=datetime.now(), required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_uom_qty = fields.Float(string='Quantity', digits=(16, 2), required=True)
    gross_unit_price = fields.Float(string='Gross Unit Price', digits='Product Price', required=True)
    # location_id = fields.Many2one('stock.location', string='Source Location')

    # need_to_order_qty = fields.Float( string='Demand', required=True, digits=(16,2))
    qty_available = fields.Float(string='Already Ordered', digits=(16, 2), compute='_compute_quantities')
    incoming_qty = fields.Float(string='Pending', digits=(16, 2), compute='_compute_quantities')
    
    # @api.onchange('product_id')
    # def _onchange_product_id(self):
    #     if self.wizard_mrp_create_rfq_ids.location_id.id :
    #         self.location_id = self.wizard_mrp_create_rfq_ids.location_id.id

    @api.onchange("product_id","product_uom_qty")
    def _onchange_gross_unit_price(self):
        for line in self:
            if not line.product_id:
                pass
            else:
                vendor_pricelist = self.env["product.supplierinfo"].search([("name","=",self.wizard_mrp_create_rfq_ids.partner_id.id),
                                                                    ("product_tmpl_id","in",[self.product_id.product_tmpl_id.id,False]),
                                                                    ("product_id","=",[self.product_id.id,False]),
                                                                    ("min_qty","<=",self.product_uom_qty),
                                                                    "|",
                                                                    ("date_start", "=", False),
                                                                    ("date_start", "<=", datetime.now().date()),
                                                                    "|",
                                                                    ("date_end", "=", False),
                                                                    ("date_end", ">=", datetime.now().date()),
                                                                    ], order="create_date desc",limit=1)
                if vendor_pricelist:
                    line.gross_unit_price = vendor_pricelist.price
                else:
                    line.gross_unit_price = 0

    @api.depends('product_id')
    def _compute_quantities(self):
        for line in self:
            warehouse = line.wizard_mrp_create_rfq_ids.location_id.get_warehouse()

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

    

class WizardMRPCreateRFQ(models.TransientModel):
    _name = 'wizard.mrp.create.rfq'
    _description = 'wizard mrp create rfq'

    mo_id = fields.Many2one('mrp.production', string='MO')
    partner_id = fields.Many2one('res.partner',required=True, string='Vendor')
    purchase_type = fields.Many2one(
        comodel_name="purchase.order.type", required=True,string="Purchase Order Type"
    )
    currency_id = fields.Many2one('res.currency',required=True, string='Currency')
    order_deadline = fields.Date(string="Order Deadline", required=True,store=True,default=datetime.now())
    order_line_ids = fields.One2many(
        comodel_name="wizard.mrp.create.rfq.line",
        inverse_name='wizard_mrp_create_rfq_ids',
        string="Order Line",
    )

    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Operation Type",
    )
    location_id = fields.Many2one('stock.location', string='Source Location')
    location_dest_id = fields.Many2one('stock.location', string='Source Location')

    # @api.onchange('picking_type_id')
    # def _onchange_picking_type_id(self):
    #     if self.picking_type_id.default_location_dest_id.id:
    #         self.location_dest_id = self.picking_type_id.default_location_dest_id.id
    #     if self.picking_type_id.default_location_src_id.id:
    #         self.location_id = self.picking_type_id.default_location_src_id.id

    def action_clear_lines_mo_create_rfq(self):
        create_rfq = []

        for mo in self:
            # ตั้งค่าค่าต่าง ๆ ที่ต้องการส่งไปยัง wizard
            partner_id = mo.partner_id.id or False
            purchase_type = mo.purchase_type.id or False
            currency_id = mo.currency_id.id or False
            order_deadline = mo.order_deadline or False

            # เก็บข้อมูลในตัวแปร create_rfq
            create_rfq.append({
                'partner_id': partner_id,
                'purchase_type': purchase_type,
                'currency_id': currency_id,
                'order_deadline': order_deadline,
            })

        move_lines = self.order_line_ids
        if move_lines:
            move_lines.unlink()
        return self.mo_id.action_open_wizard_mrp_create_rfq_no_line(create_rfq)

    def action_create_rfq(self):
        return self.generate_rfq()

    def generate_rfq(self):
        if self.order_line_ids:
            order_line_ids = []
            for order_line in self.order_line_ids:
                line = line = (0, 0, {
                    'product_id': order_line.product_id.id,
                    'name': order_line.product_id.name,
                    'gross_unit_price': order_line.gross_unit_price,
                    'product_qty': order_line.product_uom_qty,
                    # 'date': order_line.date_required,
                    # 'location_id': order_line.location_id.id,
                    'product_uom': order_line.product_id.uom_id.id,
                })
                order_line_ids.append(line)
            
            stock = self.env['purchase.order']
            stock_id = stock.create({
                'origin': self.mo_id.name,
                'partner_id': self.partner_id.id,
                'order_type': self.purchase_type.id,
                'date_order': self.order_deadline,
                'order_line': order_line_ids,
                'currency_id': self.currency_id.id,
                'is_create_rfq': True,
                'picking_type_id': self.picking_type_id.warehouse_id.in_type_id.id,
                # 'location_dest_id': self.location_dest_id.id,
                # 'location_id': self.location_id.id,
            }).id
            action = {
                'view_mode': 'form',
                'res_model': 'purchase.order',
                'type': 'ir.actions.act_window',
                'res_id': stock_id,
                'target': 'self',
            }
            return action