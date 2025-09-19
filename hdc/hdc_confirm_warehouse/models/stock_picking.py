# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools.float_utils import float_is_zero
from itertools import groupby

class Picking(models.Model):
    _inherit = "stock.picking"

    inventory_status = fields.Selection([('waiting', 'Waiting Confirm'),('progress', 'In Progress'),('done','Done'),('cancel','Cancelled')],
                                        default='waiting', string='Inventory Status',copy=False)
    warehouse_status = fields.Selection([('warehouse', 'Inprogress'),('confirmed', 'Confirmed'),('done','Done'),('cancel','Cancelled')],
                                        default='warehouse', string='Warehouse Status',copy=False)
    user_confirm_warehouse_id = fields.Many2one('res.users',string='Confirmed Warehouse',copy=False)
    user_warehouse_in_id = fields.Many2one('res.users',string='Confirmed Warehouse In',copy=False)
    user_warehouse_out_id = fields.Many2one('res.users',string='Confirmed Warehouse Out',copy=False)
    validate_user_id = fields.Many2one('res.users',string='Validate Inventory',copy=False)
    confirmed_warehouse_date = fields.Datetime('Confirmed Warehouse Date',copy=False)
    warehouse_in_date = fields.Datetime('Warehouse In',copy=False)
    warehouse_out_date = fields.Datetime('Warehouse Out',copy=False)
    validate_date = fields.Datetime('Validate Inventory Date',copy=False)
    check_access_role = fields.Selection([('warehouse', 'Warehouse'),
                                          ('inventory', 'Inventory'),
                                          ('user','Users')],
                                            compute='_compute_check_access_role', string='check access role',copy=False)
    type_of_operation = fields.Selection(related='picking_type_id.code')
    hide_validate_btn = fields.Boolean(compute='_compute_hide_validate_btn', string='hide validate')
    hide_quantity_done = fields.Boolean(compute='_compute_hide_quantity_done', string='hide quantity done')
    
    @api.depends('warehouse_status','type_of_operation')
    def _compute_hide_validate_btn(self):
        for rec in self:
            rec.hide_validate_btn = False
            if rec.type_of_operation in ['incoming','internal','outgoing'] and rec.addition_operation_types_code !='AO-06' and rec.warehouse_status == 'warehouse':
                rec.hide_validate_btn = True
            # if rec.type_of_operation == 'internal' and rec.transfers_status in ['out','draft']:
            #     rec.hide_validate_btn = True

    def action_confirm(self):
        res = super(Picking, self).action_confirm()
        if self.type_of_operation not in ['incoming','internal','outgoing']:
            self.warehouse_status = 'confirmed'
            self.inventory_status = 'progress'
        return res

    def _compute_check_access_role(self):
        for record in self:
            if self.env.user.has_group('hdc_confirm_warehouse.group_warehouse') :
                record.check_access_role = 'warehouse'
            elif self.env.user.has_group('hdc_confirm_warehouse.group_inventory') :
                record.check_access_role = 'inventory'
            else:
                record.check_access_role = 'user'

    def _force_confirm_warehouse(self):
        self.warehouse_status = 'confirmed'
        self.inventory_status = 'progress'
        self.user_confirm_warehouse_id = self.env.user.id
        self.confirmed_warehouse_date = fields.Datetime.now()
        for m in self.move_lines:
            m.user_confirm_warehouse_id = self.env.user.id
            m.confirmed_warehouse_date = fields.Datetime.now()
            if m.qty_counted > 0:
                m.auto_fill_done()
            else:
                for move_line in m.move_line_ids:
                    move_line.qty_done = 0

    def action_confirm_warehouse(self):
        for picking in self:
            if any(move.qty_counted == 0 for move in picking.move_ids_without_package):
                return {
                    'name': _('Confirm Warehouse'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'wizard.confirm.warehouse',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {'default_picking_id': picking.id,
                                'default_type_confirm':'warehouse',},
                }
            else:
                picking._force_confirm_warehouse()
        
    # def _compute_check_order_return(self):
    #     for record in self:
    #         result = super(Picking, record)._compute_check_order_return()
    #         if record.state =='done':
    #             record.warehouse_status = 'done'
    #             record.inventory_status = 'done'
    #             record.validate_user_id = record.env.user.id
    #             record.validate_date = datetime.now()
    #         return result

    def _force_confirm_warehouse_out(self):
        self.warehouse_status = 'confirmed'
        self.inventory_status = 'progress'
        self.user_warehouse_out_id = self.env.user.id
        self.warehouse_out_date = datetime.now()
        for m in self.move_lines:
            if m.transfers_qty > 0:
                m.auto_fill_done()
            else:
                for move_line in m.move_line_ids:
                    move_line.qty_done = 0

    def action_confirm_warehouse_out(self):
        for picking in self:
            if any(move.transfers_qty == 0 for move in picking.move_ids_without_package):
                return {
                    'name': _('Confirm Transfer Out'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'wizard.confirm.warehouse',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {'default_picking_id': picking.id,
                                'default_type_confirm':'warehouse_out',},
                }
            else:
                picking._force_confirm_warehouse_out()

    def force_done(self):
        for record in self:
            result = super(Picking, record).force_done()
            if record.state =='done':
                record.warehouse_status = 'done'
                record.inventory_status = 'done'
                record.validate_user_id = record.env.user.id
                record.validate_date = datetime.now()
                if record.type_of_operation == 'internal':
                    record.user_warehouse_in_id = record.env.user.id
                    record.warehouse_in_date = datetime.now()
            return result
        
    def button_validate(self):
        res = super(Picking, self).button_validate()
        # self.transfers_status = 'done'
        for rec in self:
            if rec.state =='done':
                rec.warehouse_status = 'done'
                rec.inventory_status = 'done'
                rec.validate_user_id = rec.env.user.id
                rec.validate_date = datetime.now()
                if rec.type_of_operation == 'internal':
                    rec.user_warehouse_in_id = rec.env.user.id
                    rec.warehouse_in_date = datetime.now()
        return res
    
    #--------------แก้ของborrow------------------
    def _button_validation_borrow(self):
        res = super(Picking, self)._button_validation_borrow()
        if self.state in ['done','ready_delivery']:
            self.warehouse_status = 'done'
            self.inventory_status = 'done'
            self.validate_user_id = self.env.user.id
            self.validate_date = datetime.now()
        return res
    #--------------แก้ของborrow------------------
    
    def action_cancel(self):
        result = super().action_cancel()
        self.inventory_status = 'cancel'
        self.warehouse_status = 'cancel'
        return result
    
    @api.depends('warehouse_status','type_of_operation','addition_operation_types_code')
    def _compute_hide_quantity_done(self):
        for rec in self:
            rec.hide_quantity_done = False
            if rec.type_of_operation in ['incoming','internal','outgoing'] and rec.addition_operation_types_code !='AO-06' and rec.warehouse_status == 'warehouse':
                rec.hide_quantity_done = True
            # if rec.type_of_operation == 'internal' and rec.transfers_status in ['in','draft']:
            #     rec.hide_quantity_done = True

    @api.model
    def create(self, vals):
        res = super(Picking, self).create(vals)
        for move_line in res.move_ids_without_package:
            move_line.qty_counted = move_line.product_uom_qty
            move_line.transfers_qty = move_line.product_uom_qty
        return res

class StockMove(models.Model):
    _inherit = 'stock.move'

    qty_counted = fields.Float("Counted", digits='Product Unit of Measure',copy=False)
    transfers_qty = fields.Float("Transfers", digits='Product Unit of Measure',copy=False)
    user_confirm_warehouse_id = fields.Many2one('res.users',string='Confirmed Warehouse',copy=False)
    confirmed_warehouse_date = fields.Datetime('Confirmed Warehouse Date',copy=False)

    @api.onchange("product_uom_qty")
    def _onchange_qty_counted_transfers_qty(self):
        self.qty_counted = self.product_uom_qty
        self.transfers_qty = self.product_uom_qty
    
    @api.model
    def create(self, vals):
        res = super(StockMove, self).create(vals)
        res.qty_counted = res.product_uom_qty
        res.transfers_qty = res.product_uom_qty
        return res
    
    def auto_fill_done(self):
        for move_line in self.move_line_ids:
            if move_line.qty_done == 0:
                move_line.qty_done = move_line.product_uom_qty

    @api.onchange("qty_counted")
    def _onchange_qty_counted(self):
        if self.picking_id.state == 'assigned':
            if self.picking_id.type_of_operation != 'internal':
                if self.picking_id.addition_operation_types_code != 'AO-06':
                    if self.qty_counted > self.reserved_availability:
                        raise UserError(_("สินค้ามีไม่เพียงพอ"))

    @api.onchange("transfers_qty")
    def _onchange_transfers_qty(self):
        if self.picking_id.state == 'assigned':
            if self.picking_id.type_of_operation == 'internal':
                if self.picking_id.addition_operation_types_code != 'AO-06':
                    if self.transfers_qty > self.reserved_availability:
                        raise UserError(_("สินค้ามีไม่เพียงพอ"))

class PickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    inventory_status = fields.Selection([('waiting', 'Waiting Confirm'),('progress', 'In Progress'),('done','Done'),('cancel','Cancelled')],
                                        default='waiting', string='Inventory Status',copy=False)
    warehouse_status = fields.Selection([('warehouse', 'Inprogress'),('confirmed', 'Confirmed'),('done','Done'),('cancel','Cancelled')],
                                        default='warehouse', string='Warehouse Status',copy=False)
    confirm_picking_date = fields.Datetime(string="Confirmed Warehouse Date", readonly=True,copy=False)
    user_confirm_picking = fields.Char(string="Confirmed Warehouse", readonly=True,copy=False)
    validation_picking_date = fields.Datetime(string="Validate Inventory Date", readonly=True, tracking=True,copy=False)
    user_validation_picking = fields.Char(string="Validate Inventory", readonly=True, tracking=True,copy=False)
    
    bill_status = fields.Selection([('nothing', 'Nothing To Bill'),('draft', 'Draft Biled'),('biled','Biled')],
                                        default='nothing', string='Bill Status',copy=False)
    
    hide_validate_btn = fields.Boolean(compute='_compute_hide_validate_btn', string='hide validate')

    @api.depends('warehouse_status','inventory_status')
    def _compute_hide_validate_btn(self):
        for rec in self:
            rec.hide_validate_btn = False
            if rec.warehouse_status != 'done':
                rec.hide_validate_btn = True
            elif rec.warehouse_status == 'done' and rec.inventory_status == 'done':
                rec.hide_validate_btn = True
      
    def action_confirm_warehouse_batch(self):
        self.warehouse_status = "done"
        self.inventory_status = "progress"
        self.confirm_picking_date = fields.Datetime.now()
        self.user_confirm_picking = self.env.user.name or ''
        for move in self.move_ids:
            move.picking_id.warehouse_status = "done"
            move.picking_id.inventory_status = "progress"
            move.picking_id.confirmed_warehouse_date = fields.Datetime.now()
            move.picking_id.user_confirm_warehouse_id = self.env.user.id
        return True
    
    def action_cancel(self):
        result = super(PickingBatch, self).action_cancel()
        self.warehouse_status = "cancel"
        self.inventory_status = "cancel"
        for move in self.move_ids:
            move.picking_id.warehouse_status = "cancel"
            move.picking_id.inventory_status = "cancel"
        
        return result
    
    def action_done(self):
        res = super(PickingBatch, self).action_done()
        self.warehouse_status = "done"
        self.inventory_status = "done"
        self.validation_picking_date = fields.Datetime.now()
        self.user_validation_picking = self.env.user.name or ''
        for move in self.move_ids:
            move.picking_id.warehouse_status = "done"
            move.picking_id.inventory_status = "done"
            move.picking_id.validate_date = fields.Datetime.now()
            move.picking_id.validate_user_id = self.env.user.id

        return res
    
    @api.onchange("state")
    def _onchange_state(self):
        if self.state == "done":
            self.warehouse_status = 'done'
    

    bill_ids = fields.One2many('account.move', 'stock_batch_id', string="Vendor Bills" ,copy=False)
    bill_count = fields.Integer(
        string="Bills Count",
        compute="_compute_bills_count",
        readonly=True,
    )

    @api.depends("bill_ids")
    def _compute_bills_count(self):
        for rec in self:
            rec.bill_count = len(rec.mapped("bill_ids"))

    def action_view_bills(self):
        bills = self.mapped('bill_ids')
        action = self.env.ref('account.action_move_in_invoice_type').read()[0]
        if len(bills) > 1:
            action['domain'] = [('id', 'in', bills.ids)]
        elif bills:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = bills.id
        return action
    
    def action_view_invoice(self, invoices=False):
        """This function returns an action that display existing vendor bills of
        given purchase order ids. When only one found, show the vendor bill
        immediately.
        """
        if invoices:

            result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
            # choose the view_mode accordingly
            if len(invoices) > 1:
                result['domain'] = [('id', 'in', invoices.ids)]
            elif len(invoices) == 1:
                res = self.env.ref('account.view_move_form', False)
                form_view = [(res and res.id or False, 'form')]
                if 'views' in result:
                    result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
                else:
                    result['views'] = form_view
                result['res_id'] = invoices.id
            else:
                result = {'type': 'ir.actions.act_window_close'}

            return result
    
    def create_vendor_bill(self):
        """
        Creates a draft vendor bill from the Receipt List (stock.picking.batch) without manual qty_invoiced updates.
        """
        for batch in self:

            if batch.state != 'done':
                raise UserError(f"Cannot create bill because batch '{batch.name}' is not done.")
            
            #if batch.bill_ids:
            #    raise UserError(f"A bill has already been created for batch '{batch.name}'.")
        
            if not batch.move_line_tranfer_ids:
                raise UserError("No products in the receipt list to create a bill.")

            # Get Vendor from the picking batch
            vendor = batch.partner_id
            if not vendor:
                raise UserError("No vendor specified in the receipt list.")

            bill_vals = batch._prepare_invoice()
            for move in batch.move_line_tranfer_ids:
                po_line = self.env['purchase.order.line'].search([
                    ('id', '=', move.move_id.purchase_line_id.id),
                    ('product_id', '=', move.product_id.id),
                ], limit=1)

                invoice_line_vals = {
                    'product_id': move.product_id.id,
                    'quantity': move.qty_done,
                    'price_unit': po_line.price_unit,
                    'purchase_line_id': po_line.id,
                    'tax_ids': [(6, 0, po_line.taxes_id.ids)],
                }
                bill_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

            # Create the vendor bill
            bill = self.env['account.move'].create(bill_vals)
            if bill:
                batch.write({'bill_ids': [(4, bill.id)]})
                self.bill_status = 'draft'

            return self.action_view_invoice(bill)

    def _prepare_invoice(self):
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'in_invoice')
        journal = self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))
        partner_invoice_id =  self.partner_id
        partner_bank_id = self.partner_id.commercial_partner_id.bank_ids.filtered_domain(['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)])[:1]
        invoice_vals = {
            'move_type': move_type,
            'stock_batch_id': self.id,
            #'currency_id': self.currency_id.id,
            'partner_id': partner_invoice_id.id,
            'partner_bank_id': partner_bank_id.id,
            'invoice_origin': self.name,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals