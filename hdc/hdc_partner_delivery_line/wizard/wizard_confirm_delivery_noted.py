from odoo import _, api, fields, models
from odoo.exceptions import UserError, Warning
from odoo.tools.float_utils import float_round


class ConfirmDeliveryNote(models.TransientModel):
    _inherit = "wizard.confirm.delivery.noted"

    delivery_by_id = fields.Char(related="transport_round_id.driver", readonly=True)
    transport_round_id = fields.Many2one('delivery.round',string="Transport Round", domain=[('status_active', '=', True)])
    scheduled_date = fields.Datetime(string="Scheduled Date",default=lambda self: fields.Datetime.now())
    regis_no = fields.Char(related="transport_round_id.regis_no")

    def confirm_delivery_action(self):
        search = self.env['resupply.transfer.branch.summary'].search([('id', '=', self.search_id.id)], limit=1)
        if search:
            picking_line = []
            order_line = []
            for transfer in search.summary_delivery_ids:
                if transfer.picking_id:
                    picking_line.append(transfer.picking_id.id)
            if picking_line:
                for transfer in search:
                    for move_line in transfer.summary_line_ids:
                        if move_line.picking_id.id in picking_line:
                            # condition state not assigned
                            if move_line.state == "assigned":
                                line = (0, 0, {
                                    'distribition_line_id': self.id,
                                    'so_id': move_line.so_id.id,
                                    'invoice_id': move_line.invoice_id.id,
                                    'picking_id': move_line.picking_id.id,
                                    'move_id': move_line.move_id.id,
                                    'product_id': move_line.product_id.id,
                                    'qty_available': move_line.product_id.qty_available,
                                    'qty_demand': move_line.qty_demand,
                                    'qty_reserved': move_line.qty_reserved,
                                    'uom_id': move_line.product_id.uom_id.id,
                                    })
                                order_line.append(line)
                            if move_line.state == "partially_available":
                                line = (0, 0, {
                                    'distribition_line_id': self.id,
                                    'so_id': move_line.so_id.id,
                                    'invoice_id': move_line.invoice_id.id,
                                    'picking_id': move_line.picking_id.id,
                                    'move_id': move_line.move_id.id,
                                    'product_id': move_line.product_id.id,
                                    'qty_available': move_line.product_id.qty_available,
                                    'qty_demand': move_line.qty_reserved,
                                    'qty_reserved': move_line.qty_reserved,
                                    'uom_id': move_line.product_id.uom_id.id,
                                    })
                                order_line.append(line)
            for transfer in search.summary_delivery_ids:
                if transfer.picking_id:
                    prod_no_create = []
                    prod_create = []
                    for product_trans in transfer.picking_id.move_ids_without_package:
                        if product_trans.state == "assigned":
                            match_product = self.env['search.branch.summary.line'].search([('search_id', '=', self.search_id.id), ('move_id', '=', product_trans.id)])
                            if match_product:
                                prod_no_create.append({
                                    "product_id": product_trans.product_id.id,
                                    "product_uom_qty": product_trans.product_uom_qty,
                                    "forecast_availability": product_trans.forecast_availability,
                                    "forecast_limit": False
                                })
                            else:
                                prod_create.append({
                                "product_id": product_trans.product_id.id,
                                "product_uom_qty": product_trans.product_uom_qty,
                                "forecast_availability": product_trans.forecast_availability,
                                "forecast_limit": False
                                })
                                product_trans.update({'state': 'draft'})
                        elif product_trans.state == "partially_available":
                            prod_create.append({
                                "product_id": product_trans.product_id.id,
                                "product_uom_qty": product_trans.product_uom_qty,
                                "forecast_availability": product_trans.forecast_availability,
                                "forecast_limit": True
                            })
                            prod_no_create.append({
                                "product_id": product_trans.product_id.id,
                                "product_uom_qty": product_trans.product_uom_qty,
                                "forecast_availability": product_trans.forecast_availability,
                                "forecast_limit": True
                            })
                            product_trans.update({'state': 'draft'})
                        else:
                            prod_create.append({
                                "product_id": product_trans.product_id.id,
                                "product_uom_qty": product_trans.product_uom_qty,
                                "forecast_availability": product_trans.forecast_availability,
                                "forecast_limit": False
                            })
                            product_trans.update({'state': 'draft'})

                    if prod_create and prod_no_create:
                        update_line_product = []
                        delete_line_product = []
                        new_transfer = transfer.picking_id.copy({"backorder_id": transfer.picking_id.id})
                        if new_transfer:
                            for new_product in new_transfer.move_ids_without_package:
                                for prod in prod_no_create:
                                    if prod['product_id'] == new_product.product_id.id and prod['product_uom_qty'] == new_product.product_uom_qty:
                                        if prod['forecast_limit'] == True:
                                            update_line_product.append(new_product.id)
                                        else:
                                            new_product.update({'state': 'draft'})
                                            delete_line_product.append(new_product.id)
                                if update_line_product:
                                    check_update = self.env['stock.move'].search([('id','in', update_line_product)])
                                    if check_update:
                                        for prod_update in check_update:
                                            prod_update.update({'product_uom_qty': prod['product_uom_qty'] - prod['forecast_availability']})
                                if delete_line_product:
                                    check_delete = self.env['stock.move'].search([('id','in', delete_line_product)])
                                    if check_delete:
                                        for prod_delete in check_delete:
                                            prod_delete.unlink()
                            new_transfer.action_confirm()
                            for old_product in transfer.picking_id.move_ids_without_package:
                                for prod in prod_create:
                                    if prod['product_id'] == old_product.product_id.id and prod['product_uom_qty'] == old_product.product_uom_qty:
                                        old_product.update({'state': 'draft' })
                                        if prod['forecast_limit'] == True:
                                            transfer.picking_id.do_unreserve()
                                            old_product.update({ 'product_uom_qty': prod['forecast_availability']})
                                            transfer.picking_id.action_assign()
                                        else:
                                            old_product.unlink()
                                        transfer.picking_id.action_confirm()
                
            distribition_note = self.env['distribition.delivery.note']
            distribition_note_id = distribition_note.create({
                'schedule_date': self.scheduled_date,
                # 'total_weight': self.total_weight,
                'transport_round_id': self.transport_round_id.id,
                'driver_name': self.delivery_by_id or "",
                'car_code': self.regis_no or "",
                'distribition_line_ids': order_line,
            }).id
            action = {
                'name': "Generate Distribution Delivery Note",
                'view_mode': 'form',
                'res_model': 'distribition.delivery.note',
                'type': 'ir.actions.act_window',
                'res_id': distribition_note_id,
            }
            return action
        return True