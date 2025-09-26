# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models, api
from odoo.osv import expression
from odoo.exceptions import UserError,ValidationError
from datetime import timedelta, datetime

class WizardReceiptListLine(models.TransientModel):
    _name = 'wizard.receipt.list.line'
    _description = 'Jobs Create PR Line'

    wizard_receipt_list_ids = fields.Many2one(
        comodel_name="wizard.receipt.list",
        string="jobs to create pr",
    )
    picking_id = fields.Many2one('stock.picking', string='Picking ID')
    product_categ_id = fields.Many2one('product.category', string='Product Category')
    product_id = fields.Many2one('product.product', string='Product')
    location_id = fields.Many2one('stock.location', string='Source Location')
    product_uom_qty = fields.Float(string='Demand', digits=(16, 2))
    product_uom = fields.Many2one('uom.uom',string='UOM')
    price_unit = fields.Float(string='Unit Price',)
    move_tranfer_ids = fields.Many2one('stock.move', string='Stock move')


class WizardReceiptList(models.TransientModel):
    _name = 'wizard.receipt.list'
    _description = 'wizard Jobs Create PR'

    po_id = fields.Many2one('purchase.order', string='PO')

    receipt_list_ids = fields.One2many(
        comodel_name="wizard.receipt.list.line",
        inverse_name='wizard_receipt_list_ids',
        string="Purchase estimate Line",
    )

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    operation_type_id = fields.Many2one('stock.picking.type', string='Operation Type')
    location_dest_id = fields.Many2one('stock.location', string='Desination Location')
    schedule_date = fields.Datetime(string='Scheduled Date',default=fields.Datetime.now)
    user_id = fields.Many2one(comodel_name="res.users",string="Requested By",index=True,default=lambda self: self.env.user,)

    def action_create_batch(self):
        return self.generate_batch()

    def generate_batch(self):
        if self.receipt_list_ids:
            receipt_list_ids = []
            for order_line in self.receipt_list_ids:
                line = line = (0, 0, {
                    'name': order_line.product_id.name,
                    'product_id': order_line.product_id.id,
                    'date': self.schedule_date,
                    'origin': self.po_id.origin,
                    'reference': order_line.picking_id.name,
                    'location_id': order_line.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'product_uom': order_line.product_uom.id,
                    'product_uom_qty': order_line.product_uom_qty,
                })
                receipt_list_ids.append(order_line.move_tranfer_ids.id)
            
            batch = self.env['stock.picking.batch']
            batch_id = batch.create({
                'partner_id': self.po_id.partner_id.id,
                'scheduled_date': self.schedule_date,
                'picking_type_id': self.operation_type_id.id,
                'move_tranfer_ids': receipt_list_ids,
            }).id
            action = {
                'view_mode': 'form',
                'res_model': 'stock.picking.batch',
                'type': 'ir.actions.act_window',
                'res_id': batch_id,
                'target': 'self',
            }
            return action