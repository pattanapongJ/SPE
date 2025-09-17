# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError,ValidationError
from odoo.tools.misc import clean_context

class MRPMR(models.Model):
    _name = 'mrp.mr'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'mrp request'
    _order = "create_date DESC"

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    @api.model
    def _get_default_picking_type(self):
        company_id = self.env.context.get('default_company_id', self.env.company.id)
        return self.env['stock.picking.type'].search([
            ('code', '=', 'mrp_operation'),
            ('warehouse_id.company_id', '=', company_id),
        ], limit=1).id
    
    @api.model
    def _get_domain_picking_do_type(self):
        addition = self.env["addition.operation.type"].search([("code", "=", "AO-06")], limit=1)
        picking_do_type_ids = self.env['stock.picking.type'].search([
            ("addition_operation_types", "=", addition.id),
        ])
        return [('id','in',picking_do_type_ids.ids)]
    
    @api.model
    def _get_default_picking_do_type(self):
        addition = self.env["addition.operation.type"].search([("code", "=", "AO-06")], limit=1)
        company_id = self.env.context.get('default_company_id', self.env.company.id)
        return self.env['stock.picking.type'].search([
            ("addition_operation_types", "=", addition.id),
            ("warehouse_id","=",self.picking_type_id.warehouse_id.id),
            ('warehouse_id.company_id', '=', company_id),
        ], limit=1).id

    description = fields.Char(string="Description")
    state = fields.Selection([
        ('draft', 'Draft'),
        # ('confirmed', 'Confirmed'),
        ('waiting_approve', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('delivery', 'Delivery'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, default='draft',tracking=True,copy=False)
    
    mo_count = fields.Integer(compute="_compute_mo_count", string="Number of Manufacturing",)
    hide_btn_create_mo = fields.Boolean(compute="_compute_product_line_ids", string="Hide Create MO Botton",)
    hide_btn_transfer = fields.Boolean(compute="_compute_product_line_ids", string="Hide Transfer Botton",)
    delivery_count = fields.Integer(compute="_compute_mo_count", string="Number of delivery",)
    user_request = fields.Many2one('res.users', string='Request',  default=lambda self: self.env.user, tracking=True,index=True,)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True,tracking=True)
    request_type = fields.Many2one('request.type.mr', string='Request Type', required=True, tracking=True,index=True,)
    product_type = fields.Many2one('product.type.mr', string='Product Type', required=True, tracking=True,index=True,)
    product_line_ids = fields.One2many('mr.product.list.line', 'mr_id',tracking=True,copy=True)
    operation_line_ids = fields.One2many('mr.operation.line', 'mr_id',tracking=True,copy=True)
    request_date = fields.Datetime(string='Request Date',default=fields.Datetime.now,tracking=True,)
    delivery_date = fields.Date(string='Delivery Date',default=fields.Datetime.now,tracking=True,)
    department_id  = fields.Many2one('hr.department', string='Production', required=True, tracking=True, index=True,)
    ref_no = fields.Char(string="Ref No.")
    design_group = fields.Char(string="Design Group", tracking=True,)
    remark = fields.Text(string="Remark", tracking=True,)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        tracking=True,)
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Factory',
        domain="[('code', '=', 'mrp_operation')]",
        default=_get_default_picking_type, required=True, check_company=True, tracking=True,
        readonly=True, states={'draft': [('readonly', False)]})
    picking_type_do_id = fields.Many2one(
        'stock.picking.type', 'Delivery',
        domain=lambda self: self._get_domain_picking_do_type(), tracking=True,
        default=_get_default_picking_do_type, check_company=True,)
    remark_text = fields.Text()
    delivery_method = fields.Selection([
        ('m2o', 'Make To Order'),
        ('m2c', 'Make To Stock')
    ], string='Delivery Method',default='m2o')
    total = fields.Float(string='Total', compute='_compute_amounts', store=True, digits='Product Price')
    untax_amount = fields.Float(string='Untaxed Amount', compute='_compute_amounts', store=True, digits='Product Price')
    tax_amount = fields.Float(string='Tax Amount', compute='_compute_amounts', store=True, digits='Product Price')
    sale_person = fields.Many2one('res.users', string='Sale Person', tracking=True,)
    is_modify = fields.Boolean(related='request_type.is_modify',string='Is Modify')
    product_line_modify_ids = fields.One2many('mr.product.list.modify.line', 'mr_id',tracking=True,copy=True)
    receive_count = fields.Integer(compute="_compute_mo_count", string="Number of receivey",)
    transfer_modify_count = fields.Integer(compute="_compute_mo_count", string="Number of transfer modify",)
    hide_btn_create_receive = fields.Boolean(compute="_compute_product_line_modify_ids", string="Hide Create Create Receive",)
    hide_btn_modify_transfer = fields.Boolean(compute="_compute_product_line_modify_ids", string="Hide Modify Transfer",)
    hide_btn_create_mo_modify = fields.Boolean(compute="_compute_product_line_modify_ids", string="Create MO Modify",)
    hide_btn_create_transfer_modify = fields.Boolean(compute="_compute_product_line_modify_ids", string="Hide Create Transfer Modify",)
    
    @api.depends('operation_line_ids.subtotal', 'operation_line_ids.untax_amount', 'operation_line_ids.tax_amount')
    def _compute_amounts(self):
        for rec in self:
            rec.untax_amount = sum(line.untax_amount for line in rec.operation_line_ids)
            rec.tax_amount = sum(line.tax_amount for line in rec.operation_line_ids)
            rec.total = rec.untax_amount + rec.tax_amount

    @api.onchange('picking_type_do_id')
    def _onchange_picking_type_do_id(self):
        picking_type_do_ids = self._get_domain_picking_do_type()
        return {"domain": {"picking_type_do_id": picking_type_do_ids}}
    
    @api.onchange('product_type')
    def _onchange_product_type(self):
        if self.product_type.picking_type_id :
           self.picking_type_id = self.product_type.picking_type_id
        if self.product_type.department_id :
           self.department_id = self.product_type.department_id
        if self.product_type.out_factory_picking_type_id :
            self.picking_type_do_id = self.product_type.out_factory_picking_type_id

    def _compute_mo_count(self):
        mo_ids = self.env['mrp.production'].search([('mr_id', 'in', self.ids)])
        do_ids = self.env['stock.picking'].search([('mr_id', 'in', self.ids)])
        shipping_receive = do_ids.filtered(lambda m: m.picking_type_id == self.request_type.receipt_picking_type_id)
        shipping_receive_factory = do_ids.filtered(lambda m: m.picking_type_id == self.product_type.modify_factory_picking_type_id)
        shipping_delivery = do_ids.filtered(lambda m: m.picking_type_id == self.picking_type_do_id)
        self.mo_count = len(mo_ids)
        self.delivery_count = len(shipping_delivery)
        self.receive_count = len(shipping_receive)
        self.transfer_modify_count = len(shipping_receive_factory)

    def action_open_url_design(self):
        url_design = self.design_group
        if url_design:
            return {
                'type': 'ir.actions.act_url',
                'url': url_design,
                'target': 'new',
            }
        else:
            raise UserError("Please Input Link in the Design Group.")
    
    def action_mo_ids(self):
        mo_ids = self.env['mrp.production'].search([('mr_id', '=', self.id)])
        action = {
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
        }
        if len(mo_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': mo_ids[0].id,
            })
        else:
            action.update({
                'name': _("Manufacturing Orders Generated by %s", self.name),
                'domain': [('id', 'in', mo_ids.ids)],
                'view_mode': 'tree,form',
            })
        return action
    
    def action_delivery_ids(self):
        do_ids = self.env['stock.picking'].search([('mr_id', '=', self.id),('picking_type_id', '=', self.picking_type_do_id.id)])
        action = {
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
        }
        if len(do_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': do_ids[0].id,
            })
        else:
            action.update({
                'name': _("Delivery Orders Generated by %s", self.name),
                'domain': [('id', 'in', do_ids.ids)],
                'view_mode': 'tree,form',
            })
        return action
    
    def action_confirme(self):
        for mr in self:
            for product_line in mr.product_line_ids:
                if product_line.demand_qty <= 0:
                    raise UserError(_("Please Check Demand of Product ' %s '.")%product_line.product_id.name)
        self.state= "waiting_approve"
        
    # def action_to_approve(self):
    #     self.state= "waiting_approve"

    def action_approved(self):
        self.state = "approved"

    def auto_create_transfer(self):
        if self.product_line_ids:
            picking_type_id = self.picking_type_do_id
            product_line_ids = []
            for order_line in self.product_line_ids:
                if order_line.demand_qty > 0:
                    line = line = (0, 0, {
                        'product_id': order_line.product_id.id,
                        'name': order_line.product_id.name,
                        'product_uom_qty': order_line.demand_qty,
                        # 'date': order_line.date_required,
                        'location_id': self.picking_type_id.default_location_dest_id.id,
                        'product_uom': order_line.product_id.uom_id.id,
                        'location_dest_id' : self.picking_type_do_id.default_location_src_id.id,
                    })
                    product_line_ids.append(line)
            stock = self.env['stock.picking']
            stock_id = stock.create({
                'origin': self.name,
                'remark': self.remark_text,
                'user_id': self.user_request.id,
                'scheduled_date': self.request_date,
                'move_ids_without_package': product_line_ids,
                'picking_type_id': picking_type_id.id,
                'to_warehouse': self.picking_type_id.warehouse_id.id,
                'transit_location': self.picking_type_id.warehouse_id.lot_stock_id.id,
                'location_dest_id': picking_type_id.default_location_dest_id.id,
                'location_id': picking_type_id.default_location_src_id.id,
                'mr_id': self.id,
                # 'company_id': self.env.context.get('company_id') or self.env.company.id
            }).id

    def get_need_to_order_qty_claim(self,order_line):

        return 0
    
    def action_transfer(self):
        # if all(product_line.produced_qty == product_line.demand_qty for product_line in self.product_line_ids):
            order_line_ids = []
            for order_line in self.product_line_ids:
                need_to_order_qty = order_line.produced_qty - order_line.shipping_qty
                if need_to_order_qty >0:
                    line = line = (0, 0, {
                        'product_id': order_line.product_id.id,
                        'location_id': self.picking_type_id.default_location_dest_id.id,
                        'need_to_order_qty': need_to_order_qty,
                        'product_uom': order_line.uom_id.id,
                    })
                    order_line_ids.append(line)
                else:
                    if self.request_type.is_claim == True:
                        need_to_order_qty = self.get_need_to_order_qty_claim(order_line)
                        line = line = (0, 0, {
                        'product_id': order_line.product_id.id,
                        'location_id': self.picking_type_id.default_location_dest_id.id,
                        'need_to_order_qty': need_to_order_qty,
                        'product_uom': order_line.uom_id.id,
                        })
                        order_line_ids.append(line)
                    else:
                        line = line = (0, 0, {
                        'product_id': order_line.product_id.id,
                        'location_id': self.picking_type_id.default_location_dest_id.id,
                        'need_to_order_qty': 0,
                        'product_uom': order_line.uom_id.id,
                        })
                        order_line_ids.append(line)
                    #     raise UserError(_("There is still incomplete production."))
            picking_type_id = self.picking_type_do_id
            return {
                    'type': 'ir.actions.act_window',
                    'name': 'Inter Transfer',
                    'res_model': 'wizard.mrp.mr.intertransfer',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {'default_mr_id': self.id,
                                'default_order_line_ids': order_line_ids,
                                'default_to_warehouse': self.picking_type_id.warehouse_id.id,
                                'default_transit_location': picking_type_id.default_location_dest_id.id,
                                'default_picking_type_id': picking_type_id.id,
                                'default_location_id': self.picking_type_id.default_location_dest_id.id,
                                'default_location_dest_id': picking_type_id.default_location_src_id.id,
                                },
                }
        # else:
        #     raise UserError(_("There is still incomplete production."))
        
    def action_create_mo(self):
            order_line_ids = []
            for order_line in self.product_line_ids:
                demand = order_line.demand_qty - order_line.product_qty_mo
                if demand >0:
                    line = line = (0, 0, {
                        'product_id': order_line.product_id.id,
                        'demand_qty': order_line.demand_qty,
                        'produce_qty': demand,
                        'to_be_produce': order_line.product_qty_mo,
                        'uom_id': order_line.uom_id.id,
                    })
                    order_line_ids.append(line)
            return {
                    'type': 'ir.actions.act_window',
                    'name': 'Create MO',
                    'res_model': 'wizard.mr.create.mo',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {'default_mr_id': self.id,
                                'default_order_line_ids': order_line_ids,
                                },
                }

    def action_force_done(self):
        self.state = "done"

    def action_revise(self):
        self.state= "draft"

    def action_cancel(self):
        self.state= "cancel"

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = fields.Date.context_today(self)
            vals["name"] = (
                self.env["ir.sequence"]
                .with_company(self.env.company.id)
                .next_by_code("mrp.mr.code", sequence_date=seq_date)
            )
        result = super(MRPMR, self).create(vals)
        return result

    def _compute_product_line_ids(self):
        for mr in self:
            mr.hide_btn_create_mo = False
            mr.hide_btn_transfer = False
            if mr.state == "draft":
                mr.hide_btn_create_mo = True
                mr.hide_btn_transfer = True

            if len(mr.product_line_ids)>0:
                if all(product_line.demand_qty > 0 for product_line in mr.product_line_ids):
                    if all(product_line.product_qty_mo == product_line.demand_qty for product_line in mr.product_line_ids):
                        mr.hide_btn_create_mo = True
                    if all(product_line.produced_qty == product_line.demand_qty for product_line in mr.product_line_ids):
                        if mr.delivery_method == 'm2o' and mr.state == "in_progress":
                            mr.auto_create_transfer()
                        mr.write({'state': 'delivery'})
                    if all(product_line.produced_qty == product_line.shipping_qty for product_line in mr.product_line_ids):
                        mr.hide_btn_transfer = True
                    if all(product_line.delivery_qty == product_line.demand_qty and product_line.delivery_qty > 0 for product_line in mr.product_line_ids):
                        mr.write({'state': 'done'})
                    if mr.request_type.is_claim == True:
                        if mr.state not in ["approved","in_progress","delivery"]:
                            mr.hide_btn_transfer = True
                        else:
                            mr.hide_btn_transfer = False
                        if mr.state == "cancel":
                            mr.hide_btn_multi_scrap = True
                        else:
                            mr.hide_btn_multi_scrap = False
                    elif mr.request_type.is_claim == False:
                        if mr.state not in ["in_progress","delivery"]:
                            mr.hide_btn_multi_scrap = True
                            mr.hide_btn_transfer = True
            else:
                if mr.is_modify == True:
                    mr.hide_btn_create_mo = True
                    mr.hide_btn_transfer = True
    
    def check_delivery (self):
        if self.state == 'delivery':
            for mr in self:
                if all(product_line.delivery_qty == product_line.demand_qty for product_line in mr.product_line_ids):
                    mr.write({'state': 'done'})

    def action_create_receive(self):
        product_list = []
        for line in self.product_line_modify_ids:
            remain_receive_qty = line.demand_qty_modify - line.receive_qty_modify - line.receive_qty_modify_draft
            if remain_receive_qty > 0:
                remain_receive_qty = line.demand_qty_modify - line.receive_qty_modify
                data = (0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'demand_qty_modify': line.demand_qty_modify,
                    'remain_receive_qty': remain_receive_qty,
                    'receive_qty': remain_receive_qty,
                    'product_uom': line.product_uom.id,
                })
                product_list.append(data)
        context = {
            'default_mr_id': self.id,
            'default_product_line_ids': product_list,
        }
        return {
                'type': 'ir.actions.act_window',
                'name': 'Wizard Create Receive',
                'res_model': 'wizard.mr.product.receive',
                'view_mode': 'form',
                'target': 'new',
                'context': context,
            }
    
    def action_show_recieve_ids(self):
        do_ids = self.env['stock.picking'].search([('mr_id', '=', self.id),('picking_type_id', '=', self.request_type.receipt_picking_type_id.id)])
        action = {
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
        }
        if len(do_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': do_ids[0].id,
            })
        else:
            action.update({
                'name': _("Receive Orders Generated by %s", self.name),
                'domain': [('id', 'in', do_ids.ids)],
                'view_mode': 'tree,form',
            })
        return action
    
    def action_modify_transfer(self):
        order_line_ids = []
        picking_type_id = self.product_type.modify_factory_picking_type_id
        for order_line in self.product_line_modify_ids:
            need_to_order_qty = order_line.receive_qty_modify - order_line.receive_qty_modify_factory
            # if need_to_order_qty >0:
            line = (0, 0, {
                'product_id': order_line.product_id.id,
                'location_id': self.request_type.receipt_picking_type_id.default_location_dest_id.id,
                'need_to_order_qty': need_to_order_qty,
                'product_uom': order_line.product_uom.id,
            })
            order_line_ids.append(line)

        return {
                'type': 'ir.actions.act_window',
                'name': 'Modify Transfer',
                'res_model': 'wizard.mrp.mr.intertransfer.modify',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_mr_id': self.id,
                            'default_order_line_ids': order_line_ids,
                            'default_to_warehouse': self.request_type.receipt_picking_type_id.warehouse_id.id,
                            'default_transit_location': picking_type_id.default_location_dest_id.id,
                            'default_picking_type_id': picking_type_id.id,
                            'default_location_id': self.request_type.receipt_picking_type_id.default_location_dest_id.id,
                            'default_location_dest_id': picking_type_id.default_location_src_id.id,
                            },
            }
    
    def action_show_transfer_modify_ids(self):
        do_ids = self.env['stock.picking'].search([('mr_id', '=', self.id),('picking_type_id', '=', self.product_type.modify_factory_picking_type_id.id)])
        action = {
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
        }
        if len(do_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': do_ids[0].id,
            })
        else:
            action.update({
                'name': _("Transfer Modify Order Generated by %s", self.name),
                'domain': [('id', 'in', do_ids.ids)],
                'view_mode': 'tree,form',
            })
        return action
    
    
    def action_create_mo_modify(self):
        order_line_ids = []
        for order_line in self.product_line_modify_ids:
            demand = order_line.demand_qty_modify - order_line.product_qty_mo
            if demand >0:
                line = line = (0, 0, {
                    'product_line_modify_id': order_line.id,
                    'product_id': order_line.product_id.id,
                    'demand_qty': order_line.demand_qty_modify,
                    'produce_qty': demand,
                    'to_be_produce': order_line.product_qty_mo,
                    'uom_id': order_line.product_uom.id,
                })
                order_line_ids.append(line)
        return {
                'type': 'ir.actions.act_window',
                'name': 'Create MO Modify',
                'res_model': 'wizard.mr.create.mo.modify',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_mr_id': self.id,
                            'default_order_line_ids': order_line_ids,
                            },
            }
    
    def action_transfer_modify(self):
        order_line_ids = []
        picking_type_id = self.picking_type_do_id
        for order_line in self.product_line_modify_ids:
            need_to_order_qty = order_line.produced_qty - order_line.delivery_qty_draft - order_line.delivery_qty
            if order_line.is_refurbish == False:
                product = order_line.product_id
            else:
                product = order_line.product_refurbish_id

            mo_ids = self.env['mrp.production'].search([('mr_id', '=', self.id),('product_id', '=', product.id),('state', 'in',['done'])])
            product_uom = product.uom_id
            if len(mo_ids) > 1:
                for mo in mo_ids:
                    product_uom = mo.product_uom_id
            if need_to_order_qty >0:
                line = (0, 0, {
                    'product_id': product.id,
                    'location_id': self.picking_type_id.default_location_dest_id.id,
                    'need_to_order_qty': need_to_order_qty,
                    'product_uom': product_uom.id,
                })
                order_line_ids.append(line)
            else:
                line = (0, 0, {
                    'product_id': product.id,
                    'location_id': self.picking_type_id.default_location_dest_id.id,
                    'need_to_order_qty': order_line.demand_qty_modify,
                    'product_uom': product_uom.id,
                })
                order_line_ids.append(line)

        return {
                'type': 'ir.actions.act_window',
                'name': 'Create Transfer',
                'res_model': 'wizard.mrp.mr.intertransfer.factory',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_mr_id': self.id,
                            'default_order_line_ids': order_line_ids,
                            'default_to_warehouse': self.picking_type_id.warehouse_id.id,
                            'default_transit_location': picking_type_id.default_location_dest_id.id,
                            'default_picking_type_id': picking_type_id.id,
                            'default_location_id': self.picking_type_id.default_location_dest_id.id,
                            'default_location_dest_id': picking_type_id.default_location_src_id.id,
                            },
            }
    
    def auto_create_transfer_modify(self):
        if self.product_line_modify_ids:
            picking_type_id = self.picking_type_do_id
            order_line_ids = []
            for order_line in self.product_line_modify_ids:
                need_to_order_qty = order_line.produced_qty - order_line.delivery_qty_draft - order_line.delivery_qty
                if order_line.is_refurbish == False:
                    product = order_line.product_id
                else:
                    product = order_line.product_refurbish_id
                if need_to_order_qty > 0:
                    line = line = (0, 0, {
                        'product_id': product.id,
                        'name': product.name,
                        'product_uom_qty': need_to_order_qty,
                        'location_id': self.picking_type_id.default_location_dest_id.id,
                        'product_uom': product.uom_id.id,
                        'location_dest_id' : picking_type_id.default_location_src_id.id,
                    })
                    order_line_ids.append(line)
            stock = self.env['stock.picking']
            stock_id = stock.create({
                'origin': self.name,
                'remark': self.remark_text,
                'user_id': self.user_request.id,
                'scheduled_date': self.request_date,
                'move_ids_without_package': order_line_ids,
                'picking_type_id': picking_type_id.id,
                'to_warehouse': self.picking_type_id.warehouse_id.id,
                'transit_location': self.picking_type_id.default_location_dest_id.id,
                'location_dest_id': picking_type_id.default_location_dest_id.id,
                'location_id': picking_type_id.default_location_src_id.id,
                'mr_id': self.id,
            }).id
    
    def _compute_product_line_modify_ids(self):
        for mr in self:
            mr.hide_btn_create_receive = False
            mr.hide_btn_modify_transfer = False
            mr.hide_btn_create_mo_modify = False
            mr.hide_btn_create_transfer_modify = False
            if len(mr.product_line_modify_ids)>0:
                if all(product_line.demand_qty_modify > 0 for product_line in mr.product_line_modify_ids):
                    if all((product_line.demand_qty_modify - product_line.receive_qty_modify - product_line.receive_qty_modify_draft) <= 0 for product_line in mr.product_line_modify_ids):
                        mr.hide_btn_create_receive = True
                    if all(product_line.receive_qty_modify_factory == product_line.demand_qty_modify for product_line in mr.product_line_modify_ids):
                        mr.hide_btn_modify_transfer = True
                    if all(product_line.product_qty_mo == product_line.demand_qty_modify for product_line in mr.product_line_modify_ids):
                        mr.hide_btn_create_mo_modify = True
                    if all(product_line.produced_qty == product_line.demand_qty_modify for product_line in mr.product_line_modify_ids):
                        if mr.delivery_method == 'm2o' and mr.state == "in_progress":
                            mr.auto_create_transfer_modify()
                        mr.write({'state': 'delivery'})   
                    if all(product_line.delivery_qty == product_line.demand_qty_modify and product_line.delivery_qty > 0 for product_line in mr.product_line_modify_ids):
                        mr.hide_btn_create_transfer_modify = True
                        mr.write({'state': 'done'})

    cancel_to = fields.Char(string="TO")
    cancel_remark = fields.Text(string="Remark")
    cancel_date = fields.Date(string="Cancel Date")

class MRProductListLine(models.Model):
    _name = 'mr.product.list.line'
    _description = 'MR Product List Line'

    mr_id = fields.Many2one('mrp.mr', string='MR ID', ondelete='cascade')
    product_id = fields.Many2one("product.product", string="Product",domain=[('type', '=', 'product'), ('bom_ids', '!=', False),('bom_ids.bom_line_ids.bom_id.type', '!=', 'phantom')], required=True)
    moq_stock = fields.Float(related="product_id.moq_stock", string="MOQ")
    demand_qty = fields.Float("Demand",default=0.0, required=True, index=True)
    shipping_qty = fields.Float("Shipping",default=0.0, compute='_compute_product_quantity', required=True, index=True)
    produced_qty = fields.Float("Produced",default=0.0, compute='_compute_product_quantity', index=True)
    product_qty_mo = fields.Float("To Be Produce",default=0.0, compute='_compute_product_quantity', index=True)
    ref_mr = fields.Char(related="mr_id.name", string="Reference", index=True,store=True)
    delivery_date = fields.Date(related="mr_id.delivery_date", string="Delivery Date", index=True)
    partner_id = fields.Many2one('res.partner', related="mr_id.partner_id", string="Customer", index=True,store=True)
    user_request = fields.Many2one('res.users', related="mr_id.user_request", string='Request', index=True,store=True)
    note_text = fields.Char(string="Noted")
    factory_price = fields.Float(string="Factory Price", digits='Product Price')
    ref_no = fields.Char(related="mr_id.ref_no", string="Ref. No")

    def _compute_product_quantity(self):
        for line in self:
            moves = self.env['mrp.production'].search([
                ('mr_id', '=', line.mr_id.id),('product_id', '=', line.product_id.id),
            ])
            shipping = self.env['stock.picking'].search([('mr_id', '=', line.mr_id.id),('state','not in',['cancel'])])
            done_moves = moves.filtered(lambda m: m.state == 'done')
            total_product_qty = sum(m.product_qty for m in moves)
            total_producing_qty = sum(m.qty_producing for m in done_moves)
            total_shipping = sum(m.product_uom_qty  for m in shipping.move_ids_without_package.filtered(lambda m: m.product_id == line.product_id))
            line.product_qty_mo = total_product_qty
            line.produced_qty = total_producing_qty
            line.shipping_qty = total_shipping

    delivery_qty = fields.Float("Delivery ",default=0.0, copy=False, readonly=True,help="จำนวนที่โรงงานส่งมายังฝ่ายขาย", index=True)
    package = fields.Char("Package")
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure", required=True, index=True,domain="[('category_id', '=', product_uom_category_id)]")
    state = fields.Selection(related='mr_id.state', string='Status', readonly=True, default='draft',tracking=True,copy=False, index=True,store=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.uom_id = self.product_id.uom_id.id

class MROperationLine(models.Model):
    _name = 'mr.operation.line'
    _description = 'MR operation Line'

    mr_id = fields.Many2one('mrp.mr', string='MR ID', ondelete='cascade')
    product_id = fields.Many2one("product.product", string="Product", required=True)
    name = fields.Char(string="Description", required=True)
    qty = fields.Float("Quantity",default=1.0,digits='Product Unit of Measure', required=True)
    unit_price = fields.Float("Unit Price",default=0, required=True, digits='Product Price')
    uom_id = fields.Many2one("uom.uom", string="UoM", required=True, index=True)
    subtotal = fields.Float("Subtotal",default=1.0, required=True, compute='_compute_subtotal' , digits='Product Price', store=True)
    tax_ids = fields.Many2many(comodel_name='account.tax', string="Taxes")
    untax_amount = fields.Float(string='Untaxed Amount', compute='_compute_untax_tax_amount', store=True, digits='Product Price')
    tax_amount = fields.Float(string='Tax Amount', compute='_compute_untax_tax_amount', store=True, digits='Product Price')
    tax_included = fields.Float(string='Tax Inluded', compute='_compute_untax_tax_amount', store=True, digits='Product Price')
    tax_excluded = fields.Float(string='Tax Excluded', compute='_compute_untax_tax_amount', store=True, digits='Product Price')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            rec.name = rec.product_id.display_name
            rec.unit_price = rec.product_id.lst_price
            rec.uom_id = rec.product_id.uom_id.id
    @api.depends('qty', 'unit_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.qty * rec.unit_price

    @api.onchange('qty', 'unit_price')
    def _onchange_qty_or_unit_price(self):
        for rec in self:
            rec.subtotal = rec.qty * rec.unit_price

    @api.depends('qty', 'unit_price', 'tax_ids')
    def _compute_untax_tax_amount(self):
        for rec in self:
            if rec.mr_id:
                currency = rec.mr_id.company_id.currency_id
                taxes = rec.tax_ids.compute_all(rec.unit_price, currency, rec.qty, product=rec.product_id)
                rec.tax_included = taxes['total_included']
                rec.tax_excluded = taxes['total_excluded']
                rec.tax_amount = sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                rec.untax_amount = rec.tax_excluded
                if any(tax.price_include for tax in rec.tax_ids):
                    tax_rate = sum(tax.amount for tax in rec.tax_ids if tax.price_include) / 100
                    rec.untax_amount = rec.qty * (rec.unit_price / (1 + tax_rate))
                else:
                    rec.untax_amount = rec.qty * rec.unit_price

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    mr_id = fields.Many2one('mrp.mr', string='MR',copy=False)

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for inter in self:
            if inter.state == "done":
                if inter.origin:
                    inter_pick_ids = self.env['stock.picking'].search([('name', '=', inter.origin)], limit=1)
                    if inter_pick_ids.mr_id:
                        if inter.picking_type_id.code == "incoming":
                            for product_line in inter_pick_ids.mr_id.product_line_ids:
                                for move in inter.move_ids_without_package.filtered(lambda m: m.product_id == product_line.product_id):
                                    delivery_qty = 0.0
                                    delivery_qty = product_line.delivery_qty + move.quantity_done
                                    product_line.write({'delivery_qty': delivery_qty,})
                            inter_pick_ids.mr_id.check_delivery()

        return res
    def action_confirm(self):
        res = super(StockPicking, self).action_confirm()
        if self.mr_id : 
            if self.mr_id.state == 'in_progress':
                self.mr_id.write({'state': 'delivery'})
        return res
    
class MRProductListModifyLine(models.Model):
    _name = 'mr.product.list.modify.line'
    _description = 'MR Product List Modify Line'

    mr_id = fields.Many2one('mrp.mr', string='MR ID', ondelete='cascade')
    product_id = fields.Many2one("product.product", string="Product", required=True ,domain=[('type', '=', 'product'), ('bom_ids', '!=', False)])
    name = fields.Text(string='Description', required=True)
    demand_qty_modify = fields.Float("Demand Modify",default=1.0, required=True)
    receive_qty_modify_draft = fields.Float("Waitting Receive",default=0.0, compute='_compute_product_modify_quantity')
    receive_qty_modify = fields.Float("Receive Done",default=0.0, compute='_compute_product_modify_quantity')
    receive_qty_modify_factory = fields.Float("Factory Receive Done ",default=0.0, compute='_compute_product_modify_quantity', index=True)
    product_qty_mo = fields.Float("To Be Produce",default=0.0, compute='_compute_product_modify_quantity', index=True)
    produced_qty = fields.Float("Produced",default=0.0, compute='_compute_product_modify_quantity', index=True)
    delivery_qty_draft = fields.Float("Waitting Delivery ",default=0.0, copy=False, readonly=True, index=True)
    delivery_qty = fields.Float("Delivery ",default=0.0, copy=False, readonly=True, index=True)
    product_uom = fields.Many2one('uom.uom', 'UoM',required=True, domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    note_text = fields.Char(string="Noted")

    is_refurbish = fields.Boolean(string='Is Refurbish')
    product_refurbish_id = fields.Many2one("product.product", string="Refurbished product" ,domain=[('type', '=', 'product'), ('bom_ids', '!=', False)])
    lot_ids = fields.Many2one('stock.production.lot', string='Refurbished Lots',domain="[('product_id', '=', product_refurbish_id)]")
    product_modify_detail_ids = fields.One2many('mr.product.list.modify.line.detail', 'product_line_modify_id',copy=True)

    partner_id = fields.Many2one('res.partner', related="mr_id.partner_id", string="Customer", index=True,store=True)
    ref_mr = fields.Char(related="mr_id.name", string="Reference", index=True,store=True)
    delivery_date = fields.Date(related="mr_id.delivery_date", string="Delivery Date", index=True)
    user_request = fields.Many2one('res.users', related="mr_id.user_request", string='Request', index=True,store=True)
    state = fields.Selection(related='mr_id.state', string='Status', readonly=True, default='draft',tracking=True,copy=False, index=True,store=True)

    @api.onchange('product_id')
    def product_id_change(self):
        if self.product_id:
            default_code = self.product_id.default_code or ''
            self.name = '[' + default_code + '] ' + self.product_id.name
        else:
            self.name = ''
        self.product_uom = self.product_id.uom_id.id

    def _compute_product_modify_quantity(self):
        for line in self:
            if line.is_refurbish == False:
                product = line.product_id
            else:
                product = line.product_refurbish_id

            moves = self.env['mrp.production'].search([('mr_id', '=', line.mr_id.id),('product_id', '=', product.id),('state', 'not in',['cancel'])])
            shipping = self.env['stock.picking'].search([('mr_id', '=', line.mr_id.id),('state','not in',['cancel'])])
            done_moves = moves.filtered(lambda m: m.state == 'done')
            not_done_shipping_receive = shipping.filtered(lambda m: m.state != 'done' and m.picking_type_id == line.mr_id.request_type.receipt_picking_type_id)
            done_shipping_receive = shipping.filtered(lambda m: m.state == 'done' and m.picking_type_id == line.mr_id.request_type.receipt_picking_type_id)
            done_shipping_receive_factory = shipping.filtered(lambda m: m.state == 'done' and m.picking_type_id == line.mr_id.product_type.modify_factory_picking_type_id)
            not_done_shipping_delivery = shipping.filtered(lambda m: m.state != 'done' and m.picking_type_id == line.mr_id.picking_type_do_id)
            done_shipping_delivery = shipping.filtered(lambda m: m.state == 'done' and m.picking_type_id == line.mr_id.picking_type_do_id)
            total_product_qty = sum(m.product_qty for m in moves)
            total_producing_qty = sum(m.qty_producing for m in done_moves)
            total_shipping_delivery_draft = sum(m.product_uom_qty  for m in not_done_shipping_delivery.move_ids_without_package.filtered(lambda m: m.product_id == product))
            total_shipping_delivery = sum(m.product_uom_qty  for m in done_shipping_delivery.move_ids_without_package.filtered(lambda m: m.product_id == product))
            total_receive_qty_draft = sum(m.product_uom_qty  for m in not_done_shipping_receive.move_ids_without_package.filtered(lambda m: m.product_id == line.product_id))
            total_receive_qty = sum(m.product_uom_qty  for m in done_shipping_receive.move_ids_without_package.filtered(lambda m: m.product_id == line.product_id))
            total_receive_qty_factory = sum(m.delivery_done  for m in done_shipping_receive_factory.move_ids_without_package.filtered(lambda m: m.product_id == line.product_id))
            line.product_qty_mo = total_product_qty
            line.produced_qty = total_producing_qty
            line.delivery_qty_draft = total_shipping_delivery_draft
            line.delivery_qty = total_shipping_delivery
            line.receive_qty_modify_draft = total_receive_qty_draft
            line.receive_qty_modify = total_receive_qty
            line.receive_qty_modify_factory = total_receive_qty_factory

    def open_detail_modify(self):
        view = self.env.ref('hdc_mrp_mr.mrp_mr_product_list_modify_line_detail_form')
        return {
            'name': _('Detail Modify'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mr.product.list.modify.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
            ),
        }
    
class MRProductListModifyLineDetail(models.Model):
    _name = 'mr.product.list.modify.line.detail'
    _description = 'MR Product List Modify Line Detail'

    product_line_modify_id = fields.Many2one('mr.product.list.modify.line', string='MR Modify Product Line ID', ondelete='cascade')
    type = fields.Selection([
        ('add', 'Add'),
        ('remove', 'Remove')], 'Type', default='add', required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True,)
    name = fields.Text('Description', required=True)
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial', domain="[('product_id','=', product_id)]")
    product_uom_qty = fields.Float('Quantity', default=1.0,digits='Product Unit of Measure', required=True)
    product_uom = fields.Many2one('uom.uom', 'UoM',required=True, domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')

    @api.onchange('product_id')
    def product_id_change(self):
        if self.product_id:
            default_code = self.product_id.default_code or ''
            self.name = '[' + default_code + '] ' + self.product_id.name
        else:
            self.name = ''
        self.product_uom = self.product_id.uom_id.id