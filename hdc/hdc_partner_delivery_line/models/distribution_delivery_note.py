# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import Form
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class DistributionDeliveryNote(models.Model):
    _inherit = "distribition.delivery.note"

    name = fields.Char(string="Delivery Lists",required=True, readonly=True, translate=True, default='New')
    schedule_date = fields.Datetime(string="Scheduled Date",)
    delivery_date = fields.Datetime(string="Delivery Date",)
    transport_round_id = fields.Many2one('delivery.round',string="Transport Round", domain=[('status_active', '=', True)])
    operation_type_id = fields.Many2one('stock.picking.type', string="Operation Type" , domain=[('code', '=', 'outgoing')])
    car_code = fields.Char(string="Car Registration")
    car_type = fields.Char(string="Car Type")
    driver_name = fields.Char(string="Driver")
    driver_assistant_name = fields.Char(string="Car Assistant")
    backorder_count = fields.Integer(compute="_compute_backorder_count")
    
    def cancel_status_action(self):
        self.state = "cancel"
        if self.distribition_line_ids:
            for line in self.distribition_line_ids:
                line.picking_id.write({'delivery_list_id': False})

    def prepare_action(self):
        self.state = "prepare_product"
    
    def confirm_action(self):
        self.delivery_date = fields.Datetime.now()
        self.state = "transfer"

    def validate_action(self):
        if self.distribition_line_ids:
            for line_id in self.distribition_line_ids:
                is_zero = True
                if line_id.picking_id and line_id.state_delivery == 'assigned':
                    check_move = self.env['stock.move'].search([('picking_id', '=', line_id.picking_id.id)])
                    if check_move:
                        for move_zero  in check_move:
                            if move_zero.quantity_done > 0:
                                is_zero = False
                    if not is_zero:
                        picking_ids = self.env['stock.picking'].search([('id','=', line_id.picking_id.id)])
                        if picking_ids:
                            for pick in picking_ids:
                                res_dict = pick.button_validate()
                                if res_dict != True and res_dict != None:
                                    if res_dict.get('name') == "Create Backorder?":
                                        pickings_to_backorder = pick._check_backorder()
                                        if pickings_to_backorder:
                                            context = {
                                                'active_model': 'stock.picking',
                                                'active_ids': [pick.ids],
                                                'active_id': pick.id,
                                            }
                                            wizard = self.env['stock.backorder.confirmation'].with_context(context).create({
                                                'pick_ids': res_dict.get('context').get('default_pick_ids'),
                                                'backorder_confirmation_line_ids': [(0, 0, {'to_backorder': True, 'picking_id': pick.id})]
                                            })
                                            wizard.with_context({"button_validate_picking_ids": [pick.id]}).process()
            picking_done = True
            for line_id in self.distribition_line_ids:
                if line_id.picking_id and line_id.state_delivery != 'done':
                    picking_done = False
            if picking_done:
                self.state = "done"
            else:
                self.state = "transfer"

    def action_delivery_truck(self):
        picking_ids = []
        if self.distribition_line_ids:
            for line_id in self.distribition_line_ids:
                if line_id.picking_id:
                    picking_ids.append(line_id.picking_id.id)
        return {
                'name':"Delivery",
                'view_mode':'tree,form',
                'res_model':'stock.picking',
                'type':'ir.actions.act_window',
                'domain':[('id', 'in', picking_ids)],
                # 'res_id':self.to_return_picking_ids.id
            }
    
    def action_attachment(self):
        action = self.env["ir.actions.act_window"]._for_xml_id("base.action_attachment")
        search_att_id = []
        attachment_id = self.env["ir.attachment"].search(
            [("res_model", "=", "distribition.delivery.note"), ("res_id", "=", self.ids)]
        )
        for list in attachment_id:
            search_att_id.append(list.id)

        action["domain"] = str([("id", "=", search_att_id), ("public", "!=", True)])
        action["context"] = "{'default_res_model': '%s','default_res_id': %d}" % (
            self._name,
            self.id,
        )
        return action
    
   
    def action_backorder_delivery_truck(self):
        picking_ids = []
        if self.distribition_line_ids:
            for line_id in self.distribition_line_ids:
                if line_id.picking_id:
                    picking_ids.append(line_id.picking_id.id)
        return {
                'name':"Delivery",
                'view_mode':'tree,form',
                'res_model':'stock.picking',
                'type':'ir.actions.act_window',
                'domain':[('backorder_id', 'in', picking_ids)],
                # 'res_id':self.to_return_picking_ids.id
            }
    
    def _compute_backorder_count(self):
        for rec in self:
            picking_ids = []
            if rec.distribition_line_ids:
                for line_id in rec.distribition_line_ids:
                    if line_id.picking_id:
                        picking_ids.append(line_id.picking_id.id)
            search = self.env['stock.picking'].search([('backorder_id', 'in', picking_ids)])
            rec.backorder_count = len(search)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('distribition_delivery_note_sequence') or _('New')
        res = super(DistributionDeliveryNote, self).create(vals)
        if res['distribition_line_ids']:
            for line in res['distribition_line_ids']:
                line.picking_id.write({'delivery_list_id': res.id})
        return res

    def write(self, vals):
        if vals.get('distribition_line_ids'):
            for line in vals['distribition_line_ids']:
                if line[2]:
                    product_line = self.env['distribition.delivery.note.line'].search([('distribition_line_id', '=', self.id), ('id', '=', line[1])], limit=1)
                    if product_line:
                        if product_line.move_id:
                            product_line.move_id.write({'quantity_done':line[2]['qty_done']})
        res = super(DistributionDeliveryNote, self).write(vals)
        return res
    
class DistribitionDeliveryNoteLine(models.Model):
    _inherit = "distribition.delivery.note.line"

    so_id = fields.Many2one('sale.order', string='SO No.', readonly=True)
    invoice_id = fields.Many2one( 'account.move',string='Invoice', readonly=True)
    carrier = fields.Char(string='Carrier')
    description = fields.Char(string='Note')
    payment = fields.Char(string='Payment')
    temp_receipt_no = fields.Char(string='Temp Receipt No')
    
    picking_id = fields.Many2one('stock.picking', string='Picking Delivery', readonly=True)
    partner_id = fields.Many2one(related='so_id.partner_id', string='Customer')
    state_delivery = fields.Selection(related='picking_id.state', string='Status', readonly=True)
    delivery_address = fields.Many2one(related='picking_id.partner_id', string='Delivery Address', readonly=True)
    move_id = fields.Many2one("stock.move")
