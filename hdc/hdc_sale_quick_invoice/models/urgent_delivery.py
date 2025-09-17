# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare



from werkzeug.urls import url_encode

class SearchUrgentDelivery(models.TransientModel):
    _name = "search.urgent.delivery"
    _description = "Urgent Delivery Transfer"

    name = fields.Char(string = 'Name', default = "Generate Urgent Delivery Transfer")
    is_urgent = fields.Boolean('Urgent', default=True)
    is_not_urgent = fields.Boolean('Not urgent', default=True)
    line_ids = fields.One2many('search.urgent.delivery.line', 'generate_urgent_delivery_id', string = 'Order Line')

    def action_search(self):
        self.line_ids = False
        line_ids = []
        if self.is_urgent and self.is_not_urgent:
            picking_ids = self.env['picking.lists'].search([('state', '=', 'waiting_pick'),('urgent_delivery_id', '=', False)])
        elif self.is_urgent and self.is_not_urgent == False:
            picking_ids = self.env['picking.lists'].search([('state', '=', 'waiting_pick'),('urgent_delivery_id', '=', False),('is_urgent', '=', True)])
        elif self.is_urgent == False and self.is_not_urgent:
            picking_ids = self.env['picking.lists'].search([('state', '=', 'waiting_pick'),('urgent_delivery_id', '=', False), ('is_urgent', '=', False)])
        else:
            picking_ids = self.env['picking.lists'].search([('state', '=', 'waiting_pick'),('urgent_delivery_id', '=', False)])

        for pick in picking_ids:
            line_ids.append((0, 0, {
                'picking_id': pick.id
                }))
        self.write({'line_ids': line_ids})

    def action_clear(self):
        self.line_ids = False


    def action_create(self):
        urgent_lines = []
        product_list = []
        for line in self.line_ids:
            for item in line.picking_id.list_line_ids:
                if item.product_id.id not in product_list:
                    product_list.append(item.product_id.id)
                    
                    urgent_lines.append([0, 0, {
                        "product_id": item.product_id.id,
                        "product_uom": item.product_id.uom_id.id,
                        "qty": item.qty,
                        "urgent_pick": item.qty,
                        "urgent_location_ids":[item.location_id.id],
                        "picking_list_ids":[line.picking_id.id]
                        }])
                elif item.product_id.id in product_list:
                    index = product_list.index(item.product_id.id)
                    urgent_lines[index][2]['qty'] += item.qty
                    urgent_lines[index][2]['urgent_pick'] += item.qty
                    urgent_lines[index][2]['urgent_location_ids'].append(item.location_id.id)
                    urgent_lines[index][2]['picking_list_ids'].append(line.picking_id.id)

        urgent_delivery = self.env["urgent.delivery"].create({"name": "New",
                                                              "picking_list_ids": self.line_ids.mapped("picking_id"),
                                                              "urgent_delivery_line":urgent_lines})
        action = {
            'name': 'Urgent Delivery',
            'type': 'ir.actions.act_window',
            'res_model': 'urgent.delivery',
            'res_id': urgent_delivery.id,
            'view_mode': "form",
            "domain": [("id", "=", urgent_delivery.id)],
            }
        return action

class SearchUrgentDeliveryLine(models.TransientModel):
    _name = "search.urgent.delivery.line"
    _description = "Urgent Delivery Transfer Line"

    generate_urgent_delivery_id = fields.Many2one('search.urgent.delivery', string = 'Urgent Delivery Transfer')
    picking_id = fields.Many2one('picking.lists', 'Picking')
    partner_id = fields.Many2one(related='picking_id.partner_id')
    warehouse_id = fields.Many2one(related='picking_id.warehouse_id')
    location_id = fields.Many2one(related='picking_id.location_id')
    is_urgent = fields.Boolean(related='picking_id.is_urgent')

class UrgentDelivery(models.Model):
    _name = "urgent.delivery"
    _description = "Urgent Delivery Transfer"
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string = 'Name', default = lambda self: _('New'), copy = False)
    date = fields.Datetime("Pick Date", default = fields.Datetime.now)
    delivery_date = fields.Datetime("Delivery Date")
    user_id = fields.Many2one('res.users', string = 'Responsible', tracking = True, readonly = True,
                              default = lambda self: self.env.user)
    state = fields.Selection(
        [('in_progress', 'In progress'), ('done', 'Done'), ('cancel', 'Cancelled'), ],
        string = 'Status', readonly = True, default = 'in_progress', tracking = True)

    picking_list_ids = fields.One2many('picking.lists','urgent_delivery_id', string = "Picking List")

    picking_ids = fields.One2many('stock.picking', 'urgent_delivery_id', string = 'Transfers', readonly = True, store=True, index=True)
    from_warehouse = fields.Many2one("stock.warehouse", string="To Warehouse")
    to_warehouse = fields.Many2one("stock.warehouse", string = "From Warehouse")
    transit_location = fields.Many2one("stock.location", string="Source Location")
    location_dest_id = fields.Many2one('stock.location', "Transit Location",)
    location_id = fields.Many2one('stock.location', "Destination Location",)
    urgent_delivery_line = fields.One2many('urgent.delivery.line','urgent_delivery_id', string = "Product List")
    delivery_check = fields.Boolean('Delivery Check',default=False,compute="_compute_delivery_check")
    receipt_check = fields.Boolean('Receipt Check',default=False,compute="_compute_receipt_check")
    remark = fields.Text(string="Remark", tracking=True,) 
    
    def _update_state(self):
        for rec in self:
            check = True
            for pick in rec.picking_list_ids:
                if pick.state != "done":
                    check = False
                    break
            if check == False:
                rec.state = "in_progress"
            else:
                rec.state = "done"
                rec.delivery_date = datetime.now()

    def action_inter(self):
        picking_ids = self.env['stock.picking'].search([('urgent_delivery_id', '=', self.id)])
        action = {
            'name':"Transfer Delivery & Receipts",
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
        }
        if len(picking_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': picking_ids[0].id,
            })
        else:
            action.update({
                'domain': [('id', 'in', picking_ids.ids)],
                'view_mode': 'tree,form',
            })
        return action

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('urgent_delivery') or _('New')
        result = super(UrgentDelivery, self).create(vals)
        return result

    def action_cancel(self):
        self.picking_list_ids = False
        for line in self.picking_ids:
            if line.state != 'cancel':
                raise UserError(_("Please cancel Transfer"))
        self.state = 'cancel'

    def action_open_wizard_add_urgent_delivery(self):
        context = {
            'default_urgent_delivery_id': self.id,
        }
        return {
                'type': 'ir.actions.act_window',
                'name': 'Wizard Add Urgent Delivery Transfer',
                'res_model': 'wizard.add.urgent.delivery',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }
    
    def action_open_wizard_remove_urgent_delivery(self):
        context = {
            'default_urgent_delivery_id': self.id,
        }
        return {
                'type': 'ir.actions.act_window',
                'name': 'Wizard Remove Urgent Delivery Transfer',
                'res_model': 'wizard.remove.urgent.delivery',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }
    
    @api.onchange('to_warehouse')
    def _onchange_to_warehouse(self):
        self.transit_location = self.to_warehouse.lot_stock_id.id

    @api.onchange('from_warehouse')
    def _onchange_from_warehouse(self):
        self.location_id = self.from_warehouse.lot_stock_id.id
        self.location_dest_id = self.from_warehouse.transit_location.id

    @api.depends('state', 'urgent_delivery_line')
    def _compute_delivery_check(self):
        for rec in self:
            picking_ids = rec.env['stock.picking'].search([('urgent_delivery_id', '=', rec.id),('picking_type_id','=',rec.to_warehouse.inter_transfer_delivery.id)])
            if picking_ids:
                rec.delivery_check = True
            else:
                rec.delivery_check = False

    @api.depends('state', 'urgent_delivery_line')
    def _compute_receipt_check(self):
        for rec in self:
            picking_ids = rec.env['stock.picking'].search([('urgent_delivery_id', '=', rec.id),('picking_type_id','=',rec.from_warehouse.inter_transfer_receive.id)])
            if picking_ids:
                rec.receipt_check = True
            else:
                rec.receipt_check = False

    def create_delivery(self):
        if self.to_warehouse:
            # OUTGOING ------------
            move_line = []
            company_id = self.env.company.id
            if self.to_warehouse.inter_transfer_delivery :
            # if self.to_warehouse.out_type_id:
                for move in self.urgent_delivery_line:
                    move_line.append((0, 0, {
                        "product_id": move.product_id.id,
                        "name": move.product_id.name,
                        "product_uom_qty": move.qty,
                        "product_uom": move.product_uom.id,
                        "company_id": company_id,
                        "location_id": self.transit_location.id,
                        "location_dest_id": self.location_dest_id.id,
                        "urgent_pick": move.urgent_pick,
                        "urgent_remain": move.urgent_pick,
                        "urgent_location_ids": move.urgent_location_ids,
                        }))

                picking_out = self.env["stock.picking"].create({
                    "picking_type_id": self.to_warehouse.inter_transfer_delivery.id if self.to_warehouse.inter_transfer_delivery else  self.to_warehouse.out_type_id.id,
                    "urgent_delivery_id":self.id,
                    "location_id": self.transit_location.id,
                    "location_dest_id": self.location_dest_id.id,
                    "move_lines": move_line,
                    "note":self.remark,
                    })
                self.delivery_check = True
                picking_out.action_confirm()
                action = {
                    'name': 'Transfer Delivery',
                    'type': 'ir.actions.act_window',
                    'res_model': 'stock.picking',
                    'res_id': picking_out.id, 'view_mode': 'form',
                    }
                return action
            else:
                raise ValidationError(_("Not Out Type in Warehouse"))
            
    def create_receipt(self):
        if self.to_warehouse:
            move_line = []
            company_id = self.env.company.id
            # INCOMING ------------
            if self.from_warehouse.inter_transfer_receive:
                for move in self.urgent_delivery_line:
                    qty_remain = move.qty - move.urgent_pick
                    move_line.append((0, 0, {
                        "product_id": move.product_id.id,
                        "name": move.product_id.name,
                        "product_uom_qty": move.qty,
                        "product_uom": move.product_uom.id,
                        "company_id": company_id,
                        "location_id": self.location_dest_id.id,
                        "location_dest_id": self.location_id.id,
                        "qty_remain":qty_remain,
                        "urgent_pick": move.urgent_pick,
                        "urgent_remain": move.urgent_pick,
                        "urgent_location_ids": move.urgent_location_ids,
                        }))

                picking_in = self.env["stock.picking"].create({
                    "picking_type_id": self.from_warehouse.inter_transfer_receive.id if self.from_warehouse.inter_transfer_receive else self.from_warehouse.in_type_id.id,
                    "urgent_delivery_id":self.id,
                    "location_id": self.location_dest_id.id,
                    "location_dest_id": self.location_id.id,
                    "move_lines": move_line
                    })
                picking_in.action_confirm()
                self.receipt_check = True
                if picking_in.urgent_delivery_id:
                    for move in picking_in.move_lines:
                        move.create_move_line_urgen()
                action = {
                    'name': 'Transfer Receipts',
                    'type': 'ir.actions.act_window',
                    'res_model': 'stock.picking',
                    'res_id': picking_in.id, 'view_mode': 'form',
                    }
                return action
            else:
                raise ValidationError(_("Not In Type in Warehouse"))

    def action_open_urgent_delivery_lines(self):
        self.ensure_one()
        return {
            'name': 'Urgent Delivery Transfer Lines',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'urgent.delivery.line',
            'domain': [('urgent_delivery_id', '=', self.id)],
            'context': {'default_urgent_delivery_id': self.id},
        }
    
    def button_update_qty_from_delivery(self):
        for rec in self:
            done_pickings = rec.picking_ids.filtered(lambda p: p.state == "done" and p.picking_type_id.code == "outgoing")
            if not done_pickings:
                raise ValidationError(_("No done deliveries found."))

            for picking in done_pickings:
                for move in picking.move_lines:
                    line = rec.urgent_delivery_line.filtered(lambda l: l.product_id == move.product_id)
                    if line:
                        line.qty = move.product_uom_qty
        return True

class UrgentDeliveryLine(models.Model):
    _name = "urgent.delivery.line"
    _description = "Urgent Delivery Line Transfer"

    urgent_delivery_id = fields.Many2one('urgent.delivery', string = 'Urgent Delivery Transfer')
    ud_state = fields.Selection(related="urgent_delivery_id.state")
    ud_date = fields.Datetime(related="urgent_delivery_id.date")
    ud_name = fields.Char(related="urgent_delivery_id.name")
    ud_delivery_date = fields.Datetime(related="urgent_delivery_id.delivery_date")

    product_id = fields.Many2one("product.product", string = 'Product')
    qty = fields.Float("Demand", digits = 'Product Unit of Measure')
    urgent_pick = fields.Float(string='Urgent Pick')
    urgent_location_ids = fields.Many2many('stock.location', string='Urgent Location')
    picking_list_ids = fields.Many2many('picking.lists',string = "Picking List")
    product_uom = fields.Many2one("uom.uom", string = "UOM",)
    qty_remain = fields.Float(string='Remain Stock',compute="_compute_qty_remain",)
    partner_ids = fields.Many2many(
        'res.partner',
        string='Customers',
        compute="_compute_partner_ids",
        store=False
    )

    @api.depends('picking_list_ids.partner_id')
    def _compute_partner_ids(self):
        for rec in self:
            rec.partner_ids = rec.picking_list_ids.mapped('partner_id')

    @api.depends("qty", "urgent_pick")
    def _compute_qty_remain(self):
        for rec in self:
            rec.qty_remain = rec.qty - rec.urgent_pick

    def write(self, vals):
        res = super(UrgentDeliveryLine, self).write(vals)
        for line in self:
            delivery = self.env['stock.picking'].search([
                ('urgent_delivery_id', '=', line.urgent_delivery_id.id),
                ('picking_type_id.code', '=', 'outgoing')
            ], limit=1)
            if delivery:
                move = delivery.move_lines.filtered(lambda m: m.product_id == line.product_id)
                if move:
                    if 'urgent_pick' in vals:
                        move.urgent_pick = line.urgent_pick
                        move.urgent_remain = line.urgent_pick
                    if 'urgent_location_ids' in vals:
                        move.urgent_location_ids = [(6, 0, line.urgent_location_ids.ids)]
        return res
    


