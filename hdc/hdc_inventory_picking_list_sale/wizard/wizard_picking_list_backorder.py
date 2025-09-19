# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

class WizardPickingListBackorder(models.TransientModel):
    _name = 'wizard.picking.list.backorder'
    _description = "Wizard to mark as done or create back order"

    picking_lists = fields.Many2one('picking.lists',  string = "Picking List")

    def action_close(self):
        self.picking_lists.action_done()
        list_pick = []
        for line2 in self.picking_lists.list_line_ids:
            if line2.qty_done > 0:
                if line2.picking_id.id not in list_pick:
                    list_pick.append(line2.picking_id.id)
                    picking_ids = line2.picking_id.button_validate()
                    if picking_ids != True and picking_ids != None:
                        context = {
                            'active_model': 'stock.picking',
                            'active_ids': [line2.picking_id.ids],
                            'active_id': line2.picking_id.id,
                            }
                        backorder = self.env['stock.backorder.confirmation'].with_context(context).create({
                            'pick_ids': picking_ids.get('context').get('default_pick_ids'),
                            'backorder_confirmation_line_ids': [(0, 0, {'to_backorder': True, 'picking_id': line2.picking_id.id})]
                            })
                        backorder_pick = backorder.with_context({"button_validate_picking_ids": [line2.picking_id.id]}).process()
                        picking_backorder_id = self.env['stock.picking'].search([('backorder_id', '=', line2.picking_id.id)])
                        if line2.picking_id.claim_id:
                            picking_backorder_id.claim_id = line2.picking_id.claim_id.id
                        if picking_backorder_id:
                            picking_backorder_id.do_unreserve()
                                                
                        else:
                            raise ValidationError(_("Not Product List."))
            else:
                line2.unlink()
        self.picking_lists.change_line_move_id()

    def action_backorder(self):
        self.picking_lists.action_done()
        list_pick = []
        list_item = {}
        for line2 in self.picking_lists.list_line_ids.filtered(lambda x:x.state!='cancel'):
            if line2.qty_done > 0:
                if line2.picking_id.id not in list_pick:
                    list_pick.append(line2.picking_id.id)
                    picking_ids = line2.picking_id.button_validate()
                    if picking_ids != True and picking_ids != None:
                        context = {
                            'active_model': 'stock.picking',
                            'active_ids': [line2.picking_id.ids],
                            'active_id': line2.picking_id.id,
                            }
                        backorder = self.env['stock.backorder.confirmation'].with_context(context).create({
                            'pick_ids': picking_ids.get('context').get('default_pick_ids'),
                            'backorder_confirmation_line_ids': [(0, 0, {'to_backorder': True, 'picking_id': line2.picking_id.id})]
                            })
                        backorder_pick = backorder.with_context({"button_validate_picking_ids": [line2.picking_id.id]}).process()
                        picking_backorder_id = self.env['stock.picking'].search([('backorder_id', '=', line2.picking_id.id)])
                        if line2.picking_id.claim_id:
                            picking_backorder_id.claim_id = line2.picking_id.claim_id.id
                        if picking_backorder_id:
                            for picking_backorder_line in picking_backorder_id:
                                for line in picking_backorder_line.move_lines:
                                    for line3 in self.picking_lists.list_line_ids.filtered(lambda x:x.state!='cancel'):
                                        if line.product_id == line3.product_id:
                                            location_out_id = line3.location_id.id
                                            new_qty = line3.qty - line3.qty_done
                                            if new_qty > 0:
                                                if location_out_id in list_item:
                                                    list_line = list_item.get(location_out_id)
                                                    data_list = list_line.get("list_line_ids")
                                                    data_list.append((0, 0, {
                                                        'product_id': line.product_id.id, 'move_id': line.id,
                                                        'sale_id': picking_backorder_line.sale_id.id, 'location_id': location_out_id,
                                                        'qty':new_qty, 'picking_id': line.picking_id.id, 'amount_arranged':new_qty
                                                        }))
                                                else:
                                                    list_item[location_out_id] = {
                                                        "partner_id": picking_backorder_line.partner_id.id, "location_id": location_out_id,
                                                        "origin": self.picking_lists.name,
                                                        "warehouse_id": line.warehouse_id.id, 
                                                        "list_line_ids": [(0, 0, {
                                                            'product_id': line.product_id.id,
                                                            'move_id': line.id, 'sale_id': picking_backorder_line.sale_id.id,
                                                            'location_id': location_out_id, 'qty': new_qty,
                                                            'picking_id': line.picking_id.id, 'amount_arranged':new_qty
                                                            })]
                                                        }
                        else:
                            raise ValidationError(_("Not Product List."))
        
        self.picking_lists.change_line_move_id()
                                
        res_id = []
        for item in list_item:
            picking_lists = self.env["picking.lists"].create(list_item.get(item))
            picking_lists.do_unreserve()
            res_id.append(picking_lists.id)
        for line3 in self.picking_lists.list_line_ids:
            if line3.qty_done <= 0:
                line3.unlink()
        if res_id:
            if len(res_id) > 1:
                view_mode = "tree,form"
            else:
                view_mode = "form"
                res_id = res_id[0]

            action = {
                'name': 'Picking Lists', 'type': 'ir.actions.act_window', 'res_model': 'picking.lists',
                'res_id': res_id, 'view_mode': view_mode, "domain": [("id", "in", res_id)],
                }
            return action
