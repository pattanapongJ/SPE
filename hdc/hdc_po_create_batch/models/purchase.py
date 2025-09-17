# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_create_receipt_list(self):
        batch_list = []
        for pick in self.picking_ids:
            if pick.state in ['draft','assigned']:
                for line in pick.move_ids_without_package:
                    if line.batch_id.state == 'cancel' or line.batch_id.id == False:
                        batch_list.append((0, 0, {
                            'product_id': line.product_id.id,
                            'product_categ_id': line.product_id.categ_id.id,
                            'location_id': line.location_id.id,
                            'product_uom_qty': line.product_uom_qty,
                            'product_uom': line.product_uom.id,
                            'picking_id': pick.id,
                            'price_unit':line.price_unit,
                            'move_tranfer_ids':line.id,
                        }))

        context = {
            'default_po_id': self.id,
            'default_receipt_list_ids': batch_list,
        }

        if self.picking_ids[0]:
            context.update({
                'default_warehouse_id': self.picking_ids[0].picking_type_id.warehouse_id.id,
                'default_operation_type_id': self.picking_ids[0].picking_type_id.id,
                'default_location_dest_id': self.picking_ids[0].location_dest_id.id,
            })

        return {
                'type': 'ir.actions.act_window',
                'name': 'Create Receipt List',
                'res_model': 'wizard.receipt.list',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }
    
    count_receipt_list = fields.Integer(string='receipt list count', compute='_compute_receipt_list')

    def _compute_receipt_list(self):
        for rec in self:
            move_ids = rec.env['stock.move'].search([
            ('origin', '=', rec.name),
            ('company_id', '=', rec.company_id.id),
            ('partner_id', '=', rec.partner_id.id),
            ('picking_type_id', '=', rec.picking_type_id.id),
            ('batch_id', '!=', False),])
            batch_id = []
            for move in move_ids:
                if move.batch_id.id not in batch_id:
                    batch_id.append(move.batch_id.id)
            rec.count_receipt_list = len(batch_id)
    
    def action_view_picking_list(self):
        move_ids = self.env['stock.move'].search([
            ('origin', '=', self.name),
            ('company_id', '=', self.company_id.id),
            ('partner_id', '=', self.partner_id.id),
            ('picking_type_id', '=', self.picking_type_id.id),
            ('batch_id', '!=', False),])
        batch_id = []
        for move in move_ids:
            if move.batch_id.id not in batch_id:
                batch_id.append(move.batch_id.id)
        if len(batch_id) > 1:
            view_mode = "tree,form"
        else:
            view_mode = "form"
            batch_id = batch_id[0]
        action = {
            'name': 'Receipt Lists', 
            'type': 'ir.actions.act_window', 
            'res_model': 'stock.picking.batch', 
            'res_id': batch_id,
            'view_mode': view_mode, 
            "domain": [("id", "in", batch_id)],
            }
        return action