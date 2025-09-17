# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class GeneratePickingList(models.TransientModel):
    _name = 'generate.picking.list'
    _description = "Generate Picking List"

    name = fields.Char(string='Name', default="Generate Picking List")
    partner_id = fields.Many2one("res.partner", string = "Customer", required=True)
    is_sale_id = fields.Many2many("sale.order", string = "Sale Order Check", compute='_compute_domain_sale_id', index=True)
    sale_id = fields.Many2many("sale.order", string = "Sale Order", domain="[('id', 'in', is_sale_id)]")
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse")
    location_id = fields.Many2one('stock.location', string = 'Source Location')
    order_date = fields.Date("Order Date")
    delivery_date = fields.Date("Delivery Date")
    line_ids = fields.One2many('generate.picking.list.line', 'generate_picking_list', string = 'Order Line')
    company_id = fields.Many2one("res.company", string = "Company", default=lambda self: self.env.company)
    type_pl = fields.Selection([
        ('sale','Sale'),
        ('rma','RMA')],
        string = "Type PL", default="sale" , required=True)
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', domain="[('customer','=', True)]", )

    @api.onchange('company_id')
    def get_domain_from_company(self):
        domain_sale_id = [('company_id.id', '=', self.company_id.id)]
        return {'domain': {'sale_id': domain_sale_id}}
    
    def _compute_domain_sale_id(self):
        for record in self:
            sale_value = []
            if record.partner_id:
                sale_id = self.env['sale.order'].search([('state', 'in', ('done', 'sale')), ('partner_id', '=', record.partner_id.id),('company_id', '=', record.company_id.id)])
                if record.type_pl == 'sale':
                    if record.partner_shipping_id:
                        sale_id = self.env['sale.order'].search([('state', 'in', ('done', 'sale')), ('partner_id', '=', record.partner_id.id), ('partner_shipping_id', '=', record.partner_shipping_id.id),('company_id', '=', record.company_id.id)])
            else:
                return {
                    'domain': {
                        'sale_id': [('company_id', '=', record.company_id.id)]
                        }
                    }
            for sale in sale_id:
                for pick in sale.picking_ids:
                    pick.move_lines._compute_picking_done_qty()
                    move_lines_ids = pick.move_lines.filtered(lambda l: l.state not in (
                    'cancel', 'done') and l.picking_code == 'outgoing' and l.is_done_picking == False)
                    if move_lines_ids:
                        sale_value.append(sale.id)
                        continue
            record.is_sale_id = sale_value
            return sale_value

    @api.onchange('partner_id','partner_shipping_id')
    def _onchange_partner_id(self):
        sale_value = []
        if self.partner_id:
            sale_id = self.env['sale.order'].search([('state', 'in', ('done','sale')),('partner_id', '=', self.partner_id.id),('company_id', '=', self.company_id.id)])
            if self.type_pl == 'sale':
                if self.partner_shipping_id:
                    sale_id = self.env['sale.order'].search([('state', 'in', ('done','sale')),('partner_id', '=', self.partner_id.id),('partner_shipping_id', '=', self.partner_shipping_id.id),('company_id', '=', self.company_id.id)])  
        else:
            return {
                'domain': {
                    'sale_id': [
                    ('company_id', '=', self.company_id.id)]
                    }
                }

        sale_value = self._compute_domain_sale_id()
        return {
            'domain': {
                'sale_id': [('id', 'in', sale_value)]
                }
            }

    def action_search(self):
        self.line_ids = False
        search_domain = [('partner_id', '=', self.partner_id.id),('state', 'in', ('done','sale')),('company_id', '=', self.company_id.id)]
        if self.sale_id:
            search_domain.append(('id', 'in', self.sale_id.ids))
        if self.warehouse_id:
            search_domain.append(('warehouse_id', '=', self.warehouse_id.id))
        if self.order_date:
            order_date_min = datetime.combine(self.order_date, datetime.min.time()) - relativedelta(hours = 7)
            order_date_max = datetime.combine(self.order_date, datetime.max.time()) - relativedelta(hours = 7)
            search_domain.append(('date_order', '>=', order_date_min))
            search_domain.append(('date_order', '<=', order_date_max))
        if self.partner_shipping_id:
            search_domain.append(('partner_shipping_id', '=', self.partner_shipping_id.id))
        sale_id = self.env['sale.order'].search(search_domain)

        line_ids = []
        if self.type_pl == "sale":
            for sale in sale_id:
                if sale.picking_ids:
                    for pick in sale.picking_ids.filtered(lambda l: l.claim_id.id== False):
                        pick.move_lines._compute_picking_done_qty()
                        move_lines_ids = pick.move_lines.filtered(
                            lambda l: l.state not in ('cancel', 'done') and l.picking_code == 'outgoing' and l.is_done_picking == False)

                        if self.location_id:
                            move_lines_ids = pick.move_lines.filtered(lambda l: l.location_id == self.location_id)
                        elif self.delivery_date:
                            move_lines_ids = pick.move_lines.filtered(lambda l: l.date >= datetime.combine(self.delivery_date, datetime.min.time()) - relativedelta(hours = 7) and l.date <= datetime.combine(self.delivery_date, datetime.max.time()) - relativedelta(hours = 7))
                        for move in move_lines_ids:
                            putaway_id = self.env['stock.putaway.rule'].search([('product_id', '=', move.product_id.id)],
                                                                               limit = 1)
                            if putaway_id:
                                pick_location_id = putaway_id.location_out_id.id
                            else:
                                pick_location_id = move.location_id.id
                            # picking_id_done = self.env['picking.lists.line'].search(
                            #     [('product_id', '=', move.product_id.id), ('sale_id', '=', move.sale_line_id.order_id.id),
                            #     ('picking_lists.state', '=', "done")])
                            picking_id_done = self.env['picking.lists.line'].search(
                                [('product_id', '=', move.product_id.id), ('sale_id', '=', move.sale_line_id.order_id.id),
                                ('state', '=', "done")]) # ปรับการหักลบจำนวนจาก check picking list ไป check picking list line
                            # picking_id_draft = self.env['picking.lists.line'].search(
                            #     [('product_id', '=', move.product_id.id), ('sale_id', '=', move.sale_line_id.order_id.id),
                            #     ('picking_lists.state', '=', "draft")])
                            picking_id_draft = self.env['picking.lists.line'].search(
                                [('product_id', '=', move.product_id.id), ('sale_id', '=', move.sale_line_id.order_id.id),
                                ('state', '=', "draft")]) # ปรับการหักลบจำนวนจาก check picking list ไป check picking list line
                            product_uom_qty = move.sale_line_id.product_uom_qty
                    
                            product_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', move.sale_line_id.product_id.product_tmpl_id.id),('type', '=', 'normal')], limit=1)
                            if not move.sale_line_id.order_id.type_id.modern_trade and move.sale_line_id.product_id.route_ids.filtered(lambda l: l.name == "Manufacture") and product_bom:
                                for line_bom in product_bom.bom_line_ids:
                                    if move.product_id == line_bom.product_id:
                                        product_uom_qty = line_bom.product_qty * move.sale_line_id.product_uom_qty

                            if move.product_uom.id != move.sale_line_id.product_uom.id and move.product_id.id == move.sale_line_id.product_id.id:
                                product_qty_f, procurement_uom_f = move.sale_line_id.convert_uom_factor(
                                    move.sale_line_id.product_id, product_uom_qty, move.sale_line_id.product_uom
                                )
                                product_uom_qty = product_qty_f

                            product_uom_qty = product_uom_qty - sum(picking_id_done.mapped('qty_done')) - sum(picking_id_draft.mapped('qty'))
                            cancel_qty = move.sale_line_id.cancel_qty
                            if move.product_uom.id != move.sale_line_id.product_uom.id and move.product_id.id == move.sale_line_id.product_id.id:
                                product_qty_f, procurement_uom_f = move.sale_line_id.convert_uom_factor(
                                    move.sale_line_id.product_id, move.sale_line_id.cancel_qty, move.sale_line_id.product_uom
                                )
                                cancel_qty = product_qty_f
                            product_uom_qty = product_uom_qty - abs(cancel_qty) # เคส cancel by line
                            order_line = move.sale_line_id
                            if order_line:
                                pick_location_id = order_line.pick_location_id.id
                            line_ids.append((0, 0, {
                                'name': move.product_id.name,
                                'sale_id': sale.id,
                                'product_id': move.product_id.id,
                                'location_id': move.location_id.id,
                                'pick_location_id': pick_location_id,
                                'qty': product_uom_qty,
                                'picking_id': pick.id,
                                'uom_id': move.product_uom.id,
                                'move_id': move.id,
                                'order_line': order_line.id
                                }))
        else:
            if sale_id:
                picking_ids = self.env['stock.picking'].search(
                    [('claim_id.sale_id', 'in', sale_id.ids),
                     ('state', 'not in', ("cancel", "done"))])
                for pick in picking_ids:
                    pick.move_lines._compute_picking_done_qty()
                    move_lines_ids = pick.move_lines.filtered(lambda l: l.state not in (
                    'cancel', 'done') and l.picking_code == 'outgoing' and l.is_done_picking == False)
                    if self.location_id:
                        move_lines_ids = pick.move_lines.filtered(lambda l: l.location_id == self.location_id)
                    elif self.delivery_date:
                        move_lines_ids = pick.move_lines.filtered(
                            lambda l: l.date >= datetime.combine(self.delivery_date,
                                                                 datetime.min.time()) - relativedelta(
                                hours = 7) and l.date <= datetime.combine(self.delivery_date,
                                                                          datetime.max.time()) - relativedelta(
                                hours = 7))
                    for move in move_lines_ids:
                        putaway_id = self.env['stock.putaway.rule'].search([('product_id', '=', move.product_id.id),('company_id', '=', move.company_id.id)],limit = 1)
                        if putaway_id:
                            pick_location_id = putaway_id.location_out_id.id
                        else:
                            pick_location_id = move.location_id.id

                        picking_id_done = self.env['picking.lists.line'].search(
                            [('product_id', '=', move.product_id.id), ('sale_id', '=', move.sale_line_id.order_id.id),
                            ('picking_lists.state', '=', "done")])
                        picking_id_draft = self.env['picking.lists.line'].search(
                            [('product_id', '=', move.product_id.id), ('sale_id', '=', move.sale_line_id.order_id.id),
                             ('picking_lists.state', '=', "draft")])
                        product_uom_qty = move.sale_line_id.product_uom_qty
                    
                        product_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', move.sale_line_id.product_id.product_tmpl_id.id),('type', '=', 'normal')], limit=1)
                        if not move.sale_line_id.order_id.type_id.modern_trade and move.sale_line_id.product_id.route_ids.filtered(lambda l: l.name == "Manufacture") and product_bom:
                            for line_bom in product_bom.bom_line_ids:
                                if move.product_id == line_bom.product_id:
                                    product_uom_qty = line_bom.product_qty * move.sale_line_id.product_uom_qty
                        
                        if move.product_uom.id != move.sale_line_id.product_uom.id and move.product_id.id == move.sale_line_id.product_id.id:
                            product_qty_f, procurement_uom_f = move.sale_line_id.convert_uom_factor(
                                move.sale_line_id.product_id, product_uom_qty, move.sale_line_id.product_uom
                            )
                            product_uom_qty = product_qty_f

                        product_uom_qty = product_uom_qty - sum(picking_id_done.mapped('qty_done')) - sum(picking_id_draft.mapped('qty'))
                        cancel_qty = move.sale_line_id.cancel_qty
                        if move.product_uom.id != move.sale_line_id.product_uom.id and move.product_id.id == move.sale_line_id.product_id.id:
                            product_qty_f, procurement_uom_f = move.sale_line_id.convert_uom_factor(
                                move.sale_line_id.product_id, move.sale_line_id.cancel_qty, move.sale_line_id.product_uom
                            )
                            cancel_qty = product_qty_f
                        product_uom_qty = product_uom_qty - abs(cancel_qty) # เคส cancel by line
                        order_line = self.env['sale.order.line'].search(
                                [('product_id', '=', move.product_id.id), ('order_id', '=', pick.sale_id.id)])

                        line_ids.append((0, 0, {
                            'name': move.product_id.name, 'sale_id': pick.sale_id.id, 'product_id': move.product_id.id,
                            'location_id': move.location_id.id, 'pick_location_id': pick_location_id,
                            'qty': product_uom_qty, 'picking_id': pick.id, 'uom_id': move.product_uom.id,
                            'move_id': move.id,'order_line': order_line.id
                            }))

        self.write({'line_ids': line_ids})
        self._compute_domain_sale_id()

    def action_clear(self):
        self.line_ids = False
        self._compute_domain_sale_id()

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
                        'sale_id': line.sale_id.id, 'location_id': line.location_id.id, 'amount_arranged': line.qty,
                        'picking_id': line.picking_id.id,'qty':line.qty,'order_line': line.order_line.id
                        }))
                else:
                    list_item[location_out_id] = {
                        "partner_id": line.sale_id.partner_id.id,"type_pl":self.type_pl,
                        "location_id": location_out_id,
                        "warehouse_id": line.move_id.warehouse_id.id, "list_line_ids": [(0, 0, {
                            'product_id': line.move_id.product_id.id, 'move_id': line.move_id.id,
                            'sale_id': line.sale_id.id, 'location_id': location_out_id, 'amount_arranged': line.qty,
                            'picking_id': line.picking_id.id,'qty':line.qty,'order_line': line.order_line.id,
                            'external_customer': line.external_customer.id if line.external_customer else False,'barcode_customer': line.barcode_customer,
                            'external_item': line.external_item,
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
                # if (line.qty + line.picked_qty) > line.demand_qty: # เอาออกกรณี case type RMA พี่ภูมิ
                if self.type_pl == "sale":
                    if (line.qty + line.picked_qty) > line.demand_qty:
                        raise UserError(_("จำนวน Picking QTY ต้องไม่เกินกว่าที่จำนวนสั่ง Demand."))
                else:
                    if (line.qty) > line.demand_qty:
                        raise UserError(_("จำนวน Picking QTY ต้องไม่เกินกว่าที่จำนวนสั่ง Demand."))
                if line.qty > (line.demand_qty - line.picked_qty - line.picking_draft):
                    confirm = True
                    wizard = self.env["wizard.confirm.create.picking.list"].create({"generate_picking_list": self.id,})
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

                self._compute_domain_sale_id()
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

class GeneratePickingListLine(models.TransientModel):
    _name = 'generate.picking.list.line'
    _description = "Generate Picking List Line"

    wizard_picking_list = fields.Many2one('wizard.create.picking.list', string="Wizard Create Picking List")
    generate_picking_list = fields.Many2one('generate.picking.list', string = "Generate Picking List")

    name = fields.Text(string = 'Description')
    sale_id = fields.Many2one("sale.order", string = "Sale Order")
    product_id = fields.Many2one('product.product', string = 'Product', readonly = True)
    categ_id = fields.Many2one(related = "product_id.categ_id", string='Product Category', readonly = True)
    location_id = fields.Many2one(related = "move_id.location_id", string = 'Source Location', required = True, readonly = True)
    pick_location_id = fields.Many2one('stock.location', string = 'Location')
    order_line = fields.Many2one("sale.order.line", string = "Sale Order")
    demand_qty = fields.Float(string="Demand", digits = 'Product Unit of Measure', readonly = True,compute = "_compute_qty_ava",)
    qty = fields.Float("Picking QTY", digits = 'Product Unit of Measure')
    picked_qty = fields.Float("Picked QTY", compute = "_compute_qty_ava",
                                     digits = 'Product Unit of Measure', readonly = True)
    virtual_available = fields.Float("Available Location", compute="_compute_qty_ava", digits = 'Product Unit of Measure', readonly = True)
    uom_id = fields.Many2one("uom.uom", string = "UOM", readonly = True)
    picking_id = fields.Many2one('stock.picking', 'Picking')
    move_id = fields.Many2one('stock.move', string = "Stock Moves", copy = False)
    picking_draft = fields.Float("Picking Draft", compute = "_compute_qty_draft",
                                     digits = 'Product Unit of Measure', readonly = True)

    modify_type_txt = fields.Char(string="แปลง/Type/Block") 
    plan_home = fields.Char(string="แบบบ้าน")
    room = fields.Char(string="ชั้น/ห้อง")
    external_customer = fields.Many2one('res.partner', string="External Customer",domain=[('customer','=',True)])
    external_item = fields.Char(string="External Item")
    barcode_customer = fields.Char(string="Barcode Customer")
    barcode_modern_trade = fields.Char(string="Barcode Product")
    description_customer = fields.Text(string="External Description")
    canceled_qty = fields.Float("Cancel Qty", digits = 'Product Unit of Measure')

    def _compute_qty_ava(self):
        for rec in self:
            # First Define
            rec.demand_qty = rec.order_line.product_uom_qty
            product_bom = rec.env['mrp.bom'].search([('product_tmpl_id', '=', rec.order_line.product_id.product_tmpl_id.id),('type', '=', 'normal')], limit=1)
            if not rec.sale_id.type_id.modern_trade and rec.order_line.product_id.route_ids.filtered(lambda l: l.name == "Manufacture") and product_bom:
                for line_bom in product_bom.bom_line_ids:
                    if rec.product_id == line_bom.product_id:
                        rec.demand_qty = line_bom.product_qty * rec.order_line.product_uom_qty
            else:
                # ถ้าไม่มี BoM ใช้จำนวนที่สั่งของสินค้าหลักโดยตรง
                rec.demand_qty = rec.order_line.product_uom_qty
                if rec.uom_id.id != rec.order_line.product_uom.id and rec.product_id.id == rec.order_line.product_id.id:
                    product_qty_f, procurement_uom_f = rec.order_line.convert_uom_factor(
                        rec.order_line.product_id, rec.order_line.product_uom_qty, rec.order_line.product_uom
                    )
                    rec.demand_qty = product_qty_f                   
                    
            quant_id = rec.env['stock.quant'].search([('product_id','=', rec.product_id.id),('location_id','=',rec.pick_location_id.id)])
            if quant_id:
                if len(quant_id) == 1:
                    rec.virtual_available = quant_id.available_quantity
                else:
                    virtual_available = 0
                    for quant in quant_id:
                        virtual_available += quant.available_quantity
                    rec.virtual_available = virtual_available
            else:
                rec.virtual_available = 0
            if self.generate_picking_list.type_pl == 'rma':
                picking_id = rec.env['picking.lists.line'].search(
                    [('product_id', '=', rec.product_id.id), ('sale_id', '=', rec.sale_id.id),
                    ('picking_lists.state', '=', "done"),('picking_lists.type_pl','=','rma')])
            else:
                # picking_id = rec.env['picking.lists.line'].search(
                #     [('product_id', '=', rec.product_id.id), ('sale_id', '=', rec.sale_id.id),
                #     ('picking_lists.state', '=', "done"),('picking_lists.type_pl','!=','rma')])
                picking_id = rec.env['picking.lists.line'].search(
                    [('product_id', '=', rec.product_id.id), ('sale_id', '=', rec.sale_id.id),
                    ('state', '=', "done"),('picking_lists.type_pl','!=','rma')]) # ปรับการให้การทำ stamp ไปตรวจสอบที่ระดับ line แทน
            rec.picked_qty = sum(picking_id.mapped('qty_done'))
            canceled_qty = rec.order_line.cancel_qty
            if rec.uom_id.id != rec.order_line.product_uom.id and rec.product_id.id == rec.order_line.product_id.id:
                product_qty_f, procurement_uom_f = rec.order_line.convert_uom_factor(
                    rec.order_line.product_id, rec.order_line.cancel_qty, rec.order_line.product_uom
                )
                canceled_qty = product_qty_f
            rec.canceled_qty = canceled_qty


    def _compute_qty_draft(self):
        for rec in self:
            if self.generate_picking_list.type_pl == 'rma':
                picking_id = self.env['picking.lists.line'].search(
                    [('product_id', '=', rec.product_id.id), ('sale_id', '=', rec.sale_id.id),
                    ('state', '=', "draft"),('picking_lists.type_pl','=','rma')])
            else:
                picking_id = self.env['picking.lists.line'].search(
                    [('product_id', '=', rec.product_id.id), ('sale_id', '=', rec.sale_id.id),
                    ('state', '=', "draft"),('picking_lists.type_pl','!=','rma')])
            rec.picking_draft = sum(picking_id.mapped('qty'))


class PickingList(models.Model):
    _name = 'picking.lists'
    _description = "Picking Lists"
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', default=lambda self: _('New'), copy=False, store=True)
    partner_id = fields.Many2one("res.partner", string="Customer", domain="[('customer', '=', True)]")
    date = fields.Datetime("Pick Date", default=fields.Datetime.now)
    delivery_date = fields.Datetime("Delivery Date", default=fields.Datetime.now)
    checker = fields.Many2one('res.users', string='Checker', readonly=True)
    checker_date = fields.Datetime("Checker Date", readonly=True)
    user_id = fields.Many2one('res.users', string = 'Responsible', tracking = True, readonly=True,
                              default = lambda self: self.env.user)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_pick', 'Waiting for pickup'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, default='draft', store=True)

    project_name = fields.Many2one('sale.project', string='Project Name')
    land = fields.Char(string = "แปลง", store=True)
    home = fields.Char(string = "แบบบ้าน", store=True)
    room = fields.Char(string = "ชั้น/ห้อง", store=True)
    list_line_ids = fields.One2many('picking.lists.line', 'picking_lists', string = 'Product List')
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse")
    location_id = fields.Many2one('stock.location', string = 'Location')
    show_check_availability = fields.Boolean(compute = '_compute_show_check_availability',
        help = 'Technical field used to compute whether the button "Check Availability" should be displayed.')
    origin = fields.Char(string='PL Ref.')
    sale_id = fields.Many2many("sale.order", string = "SO No.", compute = '_compute_sale_id')
    # invoice_check = fields.Boolean(string="Invoice Check", store=True)
    remark = fields.Text('Remark')
    type_pl = fields.Selection([
        ('sale','Sale'),
        ('rma','RMA')],
        string = "Type PL", default="sale")

    def name_get(self):
        res = []
        for rec in self:
            long_name = ""
            if rec.project_name:
                if long_name:
                    long_name += ","
                long_name += rec.project_name.project_name
            if rec.land:
                if long_name:
                    long_name += ","
                long_name += rec.land
            if rec.home:
                if long_name:
                    long_name += ","
                long_name += rec.home
            if rec.room:
                if long_name:
                    long_name += ","
                long_name += rec.room
            if long_name:
                name = '%s (%s)'%(rec.name,long_name)
            else:
                name = '%s'%rec.name
            res.append((rec.id, name))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        rgs = args or []
        domain = args
        vaule = []
        if name:
            search_terms = name.split(',')  # แยกคำค้นหาตามคอมม่า
            res = self.search(domain, limit = limit)
            for term in search_terms:
                term = (term.strip()).lower()  # ตัดช่องว่างที่ไม่จำเป็น เปลี่ยนข้อความที่ต้องการค้นหาเป็นตัวพิมพ์เล็กทั้งหมด
                res = res.filtered(lambda l: term in (l.name or '').lower()
                                             or term in (l.project_name.project_name or '').lower()
                                             or term in (l.land or '').lower()
                                             or term in (l.home or '').lower()
                                             or term in (l.room or '').lower())
            return res.name_get()
        return self.search(domain, limit = limit).name_get()

    def _compute_sale_id(self):
        for picking in self:
            picking.sale_id = picking.list_line_ids.mapped("sale_id").ids

    def _compute_show_check_availability(self):
        for picking in self:
            picking.show_check_availability = any(
                move.move_state in ('waiting', 'confirmed', 'partially_available') and
                float_compare(move.qty, move.reserved_availability, precision_rounding=move.uom_id.rounding)
                for move in picking.list_line_ids)

    def do_unreserve(self):
        for line in self.list_line_ids:
            line.move_id._do_unreserve()
            for line_detail in line.list_line_detail_ids:
                line_detail.unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            warehouse_id = vals.get('warehouse_id')
            warehouse = self.env['stock.warehouse'].search([('id','=',warehouse_id)])
            if warehouse:
                if any(x in warehouse.code for x in ['NA', 'NB', 'NC', 'NM']):
                    vals['name'] = self.env['ir.sequence'].with_company(warehouse.company_id).next_by_code('picking.lists.na')
                else:
                    vals['name'] = self.env['ir.sequence'].with_company(warehouse.company_id).next_by_code('picking.lists')

        return super(PickingList, self).create(vals)

    def action_auto_fill(self):
        for rec in self:
            for line in rec.list_line_ids:
                for line_detail in line.list_line_detail_ids:
                    line_detail.qty_done = line_detail.amount_arranged

    def action_available(self):
        for rec in self:
            for line in rec.list_line_ids.filtered(lambda x:x.state!='cancel'):
                line.move_id._do_unreserve()
                line._compute_qty_ava()
                amount_arranged = 0
                if line.move_id.state not in ('done', 'assigned', 'cancel'):
                    if len(line.list_line_detail_ids) == 0:
                        if line.has_tracking != 'lot':
                            line_detail = {
                                'picking_lists_line':line.id,
                                'product_id':line.product_id.id,
                                'company_id':line.company_id.id,
                                'location_id':line.location_id.id,
                                'amount_arranged':line.amount_arranged,
                                'uom_id':line.uom_id.id,
                            }
                            self.env['picking.lists.line.detail'].create(line_detail)
                        else:
                            amount_arranged = line.amount_arranged
                            quant_id = rec.env['stock.quant'].search([('product_id','=', line.product_id.id),('location_id','=',line.location_id.id)])
                            for quant in quant_id:
                                amount = 0
                                if amount_arranged > 0:
                                    qty_ava = quant.available_quantity
                                    if qty_ava > 0:
                                        if qty_ava >= amount_arranged:
                                            amount = amount_arranged
                                        else:
                                            amount = qty_ava
                                            
                                        amount_arranged -= amount
                                        line_detail = {
                                        'picking_lists_line':line.id,
                                        'product_id':line.product_id.id,
                                        'company_id':line.company_id.id,
                                        'location_id':line.location_id.id,
                                        'lot_id':quant.lot_id.id,
                                        'amount_arranged':amount,
                                        'uom_id':line.uom_id.id,
                                        }
                                        self.env['picking.lists.line.detail'].create(line_detail)
                    for line_detail in line.list_line_detail_ids:
                        prepare_move = line.move_id._prepare_move_line_vals(quantity = line_detail.amount_arranged)
                        prepare_move['location_id'] = line.location_id.id
                        prepare_move['lot_id'] = line_detail.lot_id.id
                        forced_package_id = line.move_id.package_level_id.package_id or None
                        available_quantity = line.move_id._get_available_quantity(line.location_id, package_id = forced_package_id)
                        if prepare_move:
                            move_line_id = self.env['stock.move.line'].create(prepare_move) 
                            quants = self.env['stock.quant']._update_reserved_quantity(product_id = move_line_id.product_id, location_id = line.location_id,
                                quantity = line_detail.amount_arranged , lot_id = line_detail.lot_id, strict = True)
                            # ปิดไม่ให้ reserve เต็มจำนวน
                            # line.move_id._action_assign()
                if amount_arranged > 0:
                    raise UserError(_('It is not possible to reserve more products of %s than you have in stock.', line.product_id.display_name))
                
                for line_detail in line.list_line_detail_ids:
                    line_detail.qty_done = line_detail.amount_arranged
                    
    def unlink(self):
        for rec in self:
            rec.list_line_ids.unlink()
        return super(PickingList, self).unlink()
                
    def action_confirm(self):
        for rec in self:
            if not rec.partner_id:
                raise ValidationError(_("Please select Customer."))
            if not rec.delivery_date:
                raise ValidationError(_("Please select Delivery Date."))
            if not rec.date:
                raise ValidationError(_("Please select Pick Date."))
            rec.state = "waiting_pick"
        
    def action_done(self):
        for rec in self:
            if all(check_line.qty_done == 0 for check_line in rec.list_line_ids):
                raise UserError(_("All Picking Done are zero."))
            for line0 in rec.list_line_ids:
                line0.picking_id.do_unreserve()
            for line in rec.list_line_ids:
                line._compute_qty_ava()
                if line.qty_ava < line.qty_done:
                    raise ValidationError(_("Please Check available product %s" %line.product_id.name))
                if line.qty < line.qty_done:
                    raise ValidationError(_("Picking up more products than ordered Please adjust the done again."))

                if line.move_id.state not in ('done', 'assigned', 'cancel'):
                    for line_detail in line.list_line_detail_ids:
                        prepare_move = line.move_id._prepare_move_line_vals(quantity = line_detail.qty_done)
                        prepare_move['location_id'] = line.location_id.id
                        prepare_move['qty_done'] = line_detail.qty_done
                        prepare_move['lot_id'] = line_detail.lot_id.id
                        
                        if prepare_move:
                            move_line_id = self.env['stock.move.line'].create(prepare_move)
                            quants = self.env['stock.quant']._update_reserved_quantity(product_id = move_line_id.product_id, location_id = move_line_id.location_id,
                                quantity = move_line_id.product_uom_qty, lot_id = move_line_id.lot_id, strict = True)
                            line.move_id.write({'state': 'assigned'})
            rec.state = "done"
            rec.checker = self.env.user.id
            rec.checker_date = datetime.now()

    def change_line_move_id(self):
        for rec in self:
            for line in rec.list_line_ids:
                picking_id = rec.env['picking.lists.line'].search(
                        [('product_id', '=', line.product_id.id), ('sale_id', '=', line.sale_id.id),
                        ('picking_lists.state', '!=', ['done','cancel'])])
                if picking_id:
                    move_id = self.env['stock.move'].search(
                                            [('product_id', '=', line.product_id.id), ('sale_line_id.order_id', '=', line.sale_id.id) ,('state','!=', ['done','cancel'])])
                    for line2 in picking_id:
                        line2.move_id = move_id
                        line2.move_id._do_unreserve()

    def action_validate(self):
        for rec in self:
            for line2 in rec.list_line_ids:
                pickings_to_backorder = False
                if line2.qty_done < line2.qty:
                    pickings_to_backorder = True
                if pickings_to_backorder:
                    return {
                        'name': _('Create Backorder?'),
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'wizard.picking.list.backorder',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {"default_picking_lists": self.id},
                    }
            rec.action_done()
            list_pick = []
            list_item = {}
            for line2 in self.list_line_ids:
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
            
            rec.change_line_move_id()

    def action_cancel(self):
        for rec in self:
            if rec.state != 'done':
                for line in rec.list_line_ids:
                    line.move_id._do_unreserve()
                    line.move_id = False
            rec.state = "cancel"

class PickingListLine(models.Model):
    _name = 'picking.lists.line'
    _description = "Picking List Line"

    picking_lists = fields.Many2one('picking.lists',  string = "Picking List", copy = False)
    move_id = fields.Many2one('stock.move', string = "Stock Moves", copy = False)
    product_id = fields.Many2one("product.product", string = 'Product', readonly = True)
    categ_id = fields.Many2one(related = "product_id.categ_id", string = 'Product Category', readonly = True)
    move_location_id = fields.Many2one(related = "picking_lists.location_id")
    location_id = fields.Many2one("stock.location", string = 'Source Location', required = True, readonly = False,
                                  domain="[('id', 'child_of', move_location_id), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    sub_location_id = fields.Many2one('sub.locations', string="Sub Location")
    qty_ava = fields.Float("Available Location", compute="_compute_qty_ava", digits = 'Product Unit of Measure', readonly = True)
    sale_id = fields.Many2one("sale.order", string = "Sale Order", readonly = True )
    qty = fields.Float("Demand", digits = 'Product Unit of Measure', readonly = True)
    qty_done = fields.Float(compute="_compute_qty_done",string="Done", digits = 'Product Unit of Measure')
    picking_done_qty = fields.Float(related = "move_id.product_uom_qty", string="Picking Done QTY")
    picking_id = fields.Many2one(related = "move_id.picking_id", string = 'Picking')
    uom_id = fields.Many2one(related = "move_id.product_uom", string = "UOM", readonly = True)
    # state = fields.Selection(related = "picking_lists.state", store=True) # ต้องการปรับการของ field state แต่เป็น field relate เลย overwrite ไม่ได้
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_pick', 'Waiting for pickup'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, default='draft', store=True)
    move_state = fields.Selection(related = "move_id.state")
    company_id = fields.Many2one(related = "move_id.company_id")
    date_order = fields.Datetime(related = "sale_id.date_order")
    delivery_date = fields.Datetime(related = "sale_id.commitment_date")
    reserved_availability = fields.Float(related = "move_id.reserved_availability")
    amount_arranged = fields.Float(string="Picking QTY")
    order_line = fields.Many2one("sale.order.line", string = "Sale Order")
    qty_sale_order = fields.Float(compute="_compute_qty_sale_order",string="SO Demand", digits = 'Product Unit of Measure', readonly = True)
    has_tracking = fields.Selection(related='product_id.tracking', string='Product with Tracking')
    list_line_detail_ids = fields.One2many('picking.lists.line.detail', 'picking_lists_line', string = 'Product List Line Detail')
    
    modify_type_txt = fields.Char(string="แปลง/Type/Block") 
    plan_home = fields.Char(string="แบบบ้าน")
    room = fields.Char(string="ชั้น/ห้อง")

    external_customer = fields.Many2one('res.partner', string="External Customer",domain=[('customer','=',True)])
    external_item = fields.Char(string="External Item")
    barcode_customer = fields.Char(string="Barcode Customer")
    barcode_modern_trade = fields.Char(string="Barcode Product")
    description_customer = fields.Text(string="External Description")
    invoice_id = fields.Many2one('account.move', string='Invoice', copy = False) 
    invoice_state = fields.Selection(related='invoice_id.state',string="Invoice Status")
    sequence2 = fields.Integer(
        related="order_line.sequence2",
        string="No",
        readonly=True,
    )
    def _compute_qty_ava(self):
        for rec in self:
            quant_id = rec.env['stock.quant'].search([('product_id','=', rec.product_id.id),('location_id','=',rec.location_id.id)])
            if quant_id:
                if len(quant_id) == 1:
                    rec.qty_ava = quant_id.available_quantity
                else:
                    qty_ava = 0
                    for quant in quant_id:
                        qty_ava += quant.available_quantity
                    rec.qty_ava = qty_ava
            else:
                rec.qty_ava = 0

    def _compute_qty_sale_order(self):
        for rec in self:
            if not rec.order_line:
                order_line = self.env['sale.order.line'].search(
                                    [('product_id', '=', rec.move_id.product_id.id), ('order_id', '=', rec.sale_id.id)])
                rec.order_line = order_line
            rec.qty_sale_order = rec.order_line.product_uom_qty

    @api.onchange("qty_done")
    def _onchange_qty_done(self):
        if self.qty_done > self.qty:
            self.qty_done = False
            raise UserError(_("จำนวน Picking Done ต้องไม่เกินกว่าที่จำนวนสั่ง Demand"))
        
    @api.onchange("amount_arranged")
    def _onchange_amount_arranged(self):
        if self.amount_arranged > self.qty:
            self.amount_arranged = False
            raise UserError(_("จำนวน Picking QTY ต้องไม่เกินกว่าที่จำนวนสั่ง Demand"))
        
    def action_show_details(self):
        self.ensure_one()

        view = self.env.ref('hdc_inventory_picking_list_sale.view_picking_lists_line_detail')

        return {
            'name': _('Picking List Line Detail'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'picking.lists.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
            ),
        }
    
    def _compute_qty_done(self):
        for rec in self:
            qty_done = 0
            for line_detail in rec.list_line_detail_ids:
                qty_done += line_detail.qty_done
            
            rec.qty_done = qty_done
    
    def confirm_detail(self):
        qty_done = 0
        for line_detail in self.list_line_detail_ids:
            qty_done += line_detail.qty_done
        if qty_done > self.qty:
            raise UserError(_("จำนวน Picking Done ต้องไม่เกินกว่าที่จำนวนสั่ง Demand"))
        
    @api.onchange("list_line_detail_ids")
    def _onchange_list_line_detail_ids(self):
        if len(self.list_line_detail_ids) > 1 and not(self.has_tracking == 'lot'):
            raise UserError(_("ไม่สามารถระบุ Picking List Line Detail ได้มากกว่า 1 รายการ เนื่องจากสินค้าชิ้นนี้ไม่มี lot"))

class PickingListLineDetail(models.Model):
    _name = 'picking.lists.line.detail'
    _description = "Picking List Line Detail"

    picking_lists_line = fields.Many2one('picking.lists.line',  string = "Picking List Line", copy = False)
    product_id = fields.Many2one("product.product", string = 'Product', readonly = True)
    company_id = fields.Many2one(related = "picking_lists_line.company_id")
    location_id = fields.Many2one(related = "picking_lists_line.location_id")
    lot_id = fields.Many2one(
        'stock.production.lot', 'Lot/Serial Number',
        domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]", check_company=True)
    qty_ava = fields.Float("Available Location", compute="_compute_qty_ava", digits = 'Product Unit of Measure', readonly = True)
    amount_arranged = fields.Float(string="Picking QTY")
    reserved_availability = fields.Float(string="Reserved",compute="_compute_reserved_availability",readonly = True)
    qty_done = fields.Float("Done", digits = 'Product Unit of Measure')
    uom_id = fields.Many2one(related = "picking_lists_line.uom_id", string = "UOM", readonly = True)
    
    @api.depends("lot_id")
    def _compute_qty_ava(self):
        for rec in self:
            quant_id = rec.env['stock.quant'].search([('product_id','=', rec.product_id.id),('location_id','=',rec.location_id.id),('lot_id','=',rec.lot_id.id)])
            if quant_id:
                rec.qty_ava = quant_id.available_quantity
            else:
                rec.qty_ava = 0

    @api.depends("product_id","lot_id")
    def _compute_reserved_availability(self):
        for rec in self:
            move_line_id = rec.env['stock.move.line'].search([('move_id','=', rec.picking_lists_line.move_id.id),('product_id','=', rec.product_id.id),('location_id','=',rec.location_id.id),('lot_id','=',rec.lot_id.id)])
            rec.reserved_availability = move_line_id.product_uom_qty

    @api.onchange("qty_done")
    def _onchange_qty_done(self):
        qty_done = 0
        for line_detail in self.picking_lists_line.list_line_detail_ids:
            str_id = str(line_detail.id)
            if 'virtual' in str_id or line_detail._origin.id:
                qty_done += line_detail.qty_done
        if qty_done > self.picking_lists_line.qty:
            self.qty_done = False
            raise UserError(_("จำนวน Picking Done ต้องไม่เกินกว่าที่จำนวนสั่ง Demand"))
        
    @api.onchange("amount_arranged")
    def _onchange_amount_arranged(self):
        amount_arranged = 0
        for line_detail in self.picking_lists_line.list_line_detail_ids:
            str_id = str(line_detail.id)
            if 'virtual' in str_id or line_detail._origin.id:
                amount_arranged += line_detail.amount_arranged
        if amount_arranged > self.picking_lists_line.qty:
            self.amount_arranged = False
            raise UserError(_("จำนวน Picking QTY ต้องไม่เกินกว่าที่จำนวนสั่ง Demand"))
        
    @api.onchange("lot_id")
    def _onchange_lot_id(self):
        list_lot = []
        for line_detail in self.picking_lists_line.list_line_detail_ids:
            str_id = str(line_detail.id)
            if 'virtual' in str_id or line_detail._origin.id:
                if line_detail.lot_id.id not in list_lot:
                    list_lot.append(line_detail.lot_id.id)
                elif line_detail.lot_id.id in list_lot:
                    raise UserError(_("ห้ามระบุ Lot/Serial Number ซ้ำ"))

