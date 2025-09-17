# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError,ValidationError

class WizardCreatePickingList(models.TransientModel):
    _name = 'wizard.create.picking.list'
    _description = "Wizard Create Picking List"

    warehouse_id = fields.Many2one(comodel_name = "stock.warehouse", string = "Warehouse", required=True, readonly=True)
    location_id = fields.Many2one('stock.location', string = 'Source Location', required=True, readonly=True)
    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type',required=True, readonly=True)
    scheduled_date = fields.Datetime(string="Scheduled Date")
    user_id = fields.Many2one('res.users', string = 'Requested by', readonly = True, required = True, default = lambda self: self.env.user.id)
    line_ids = fields.One2many('generate.picking.list.line', 'wizard_picking_list', string = 'Order Line')
    project_name = fields.Many2one('sale.project', string='Project Name')
    land = fields.Char(string = "แปลง")
    home = fields.Char(string = "แบบบ้าน")
    room = fields.Char(string = "ชั้น/ห้อง")
    remark = fields.Text('Remark')

    def create_picking(self):
        list_item = {}
        if self.line_ids:
            for line in self.line_ids:
                if line.qty > (line.demand_qty - line.picked_qty - line.picking_draft):
                    picking_id = self.env['picking.lists.line'].search(
                        [('product_id', '=', line.product_id.id), ('sale_id', '=', line.sale_id.id),
                        ('picking_lists.state', '=', "draft")])
                    for pl in picking_id:
                        if pl.picking_lists.state == "draft":
                            pl.picking_lists.action_cancel()
                if line.pick_location_id:
                    location_out_id = line.pick_location_id.id
                else:
                    location_out_id = line.location_id.id
                if location_out_id in list_item:
                    list_line = list_item.get(location_out_id)
                    data_list = list_line.get("list_line_ids")
                    data_list.append((0, 0, {
                        'product_id': line.move_id.product_id.id, 'move_id': line.move_id.id,
                        'sale_id': line.sale_id.id, 'location_id': location_out_id, 'amount_arranged': line.qty,
                        'picking_id': line.picking_id.id,'qty':line.qty,'order_line': line.order_line.id,
                        'external_customer': line.external_customer.id if line.external_customer else False,'barcode_customer': line.barcode_customer,
                        'external_item': line.external_item,
                        'barcode_modern_trade': line.barcode_modern_trade,'description_customer': line.description_customer,
                        'modify_type_txt': line.modify_type_txt,'plan_home': line.plan_home,
                        'room': line.room,
                        }))
                else:
                    list_item[location_out_id] = {
                        "partner_id": line.sale_id.partner_id.id,
                        "location_id": location_out_id,
                        "project_name": self.project_name.id,
                        "land": self.land,
                        "home": self.home,
                        "room": self.room,
                        "remark": self.remark,
                        "warehouse_id": line.move_id.warehouse_id.id, "list_line_ids": [(0, 0, {
                            'product_id': line.move_id.product_id.id, 'move_id': line.move_id.id,
                            'sale_id': line.sale_id.id, 'location_id': location_out_id, 'amount_arranged': line.qty,
                            'picking_id': line.picking_id.id,'qty':line.qty,'order_line': line.order_line.id,
                            'external_customer': line.external_customer.id if line.external_customer else False,
                            'external_item': line.external_item,
                            'barcode_customer': line.barcode_customer,
                            'barcode_modern_trade': line.barcode_modern_trade,'description_customer': line.description_customer,
                            'modify_type_txt': line.modify_type_txt,'plan_home': line.plan_home,
                            'room': line.room,
                            })]
                        }

        res_id = []
        for item in list_item:
            picking_lists = self.env["picking.lists"].create(list_item.get(item))
            res_id.append(picking_lists.id)

        return res_id

    def action_create_picking(self):
        confirm_wizard = False
        if self.line_ids:
            for line in self.line_ids:
                if line.qty <= 0:
                    raise UserError(_("จำนวน Picking QTY ต้องมากกว่า 0"))
                if (line.qty + line.picked_qty) > line.demand_qty:
                    raise UserError(_("จำนวน Picking QTY ต้องไม่เกินกว่าที่จำนวนสั่ง Demand."))
                elif line.qty > (line.demand_qty - line.picked_qty - line.picking_draft):
                    confirm = True
                    wizard = self.env["wizard.confirm.create.picking.list"].create({"create_picking_list": self.id,})
                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'Confirm Create Picking',
                        'res_model': 'wizard.confirm.create.picking.list',
                        'view_mode': 'form',
                        'target': 'new',
                        'res_id': wizard.id,
                    }
            
            if confirm_wizard == False:
                res_id = self.create_picking()
                if len(res_id) > 1:
                    view_mode = "tree,form"
                else:
                    view_mode = "form"
                    res_id = res_id[0]
                action = {
                    'name': 'Picking Lists',
                    'type': 'ir.actions.act_window',
                    'res_model': 'picking.lists',
                    'res_id': res_id,
                    'view_mode': view_mode,
                    "domain": [("id", "in", res_id)],
                    }
                return action
        else:
            raise ValidationError(_("Not Product List."))