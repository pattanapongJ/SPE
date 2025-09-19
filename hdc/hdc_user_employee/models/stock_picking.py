# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools.float_utils import float_is_zero
from itertools import groupby

class Picking(models.Model):
    _inherit = "stock.picking"

    def _default_employee(self):
        employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id), ("company_id", "=", self.env.user.company_id.id)], limit=1)
        if not employee_id:
            employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)], limit=1)
        return employee_id.id
    
    user_confirm_warehouse_id = fields.Many2one('res.users',string='Confirmed Warehouse user',copy=False)
    user_confirm_warehouse_employee_id = fields.Many2one('hr.employee', string = 'Confirmed Warehouse',copy=False)
    user_warehouse_in_id = fields.Many2one('res.users',string='Confirmed Warehouse In user',copy=False)
    user_warehouse_in_employee_id = fields.Many2one('hr.employee', string = 'Confirmed Warehouse In',copy=False)
    user_warehouse_out_id = fields.Many2one('res.users',string='Confirmed Warehouse Out user',copy=False)
    user_warehouse_out_employee_id = fields.Many2one('hr.employee', string = 'Confirmed Warehouse Out',copy=False)
    validate_user_id = fields.Many2one('res.users',string='Validate Inventory user',copy=False)
    validate_user_employee_id = fields.Many2one('hr.employee', string = 'Validate Inventory',copy=False)
    user_id = fields.Many2one("res.users", string="Salesperson user")
    user_employee_id = fields.Many2one('hr.employee', string = 'Salesperson', index = True, tracking = 2,domain="[('id', 'in', sale_employee_ids)]",states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)
    requestor_emp = fields.Many2one("res.users", string="Requestor user", default=lambda self: self.env.user)
    requestor_emp_employee = fields.Many2one('hr.employee', string='Requestor', default=lambda self: self._default_employee())

    def search_employee(self):
        employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id), ("company_id", "=", self.env.user.company_id.id)], limit=1)
        if not employee_id:
            employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)], limit=1)
        return employee_id.id
    
    @api.depends('team_id')
    def _compute_sale_employee_ids(self):
        for rec in self:
            rec.sale_employee_ids = rec.team_id.sale_employee_ids.ids

    sale_employee_ids = fields.Many2many('hr.employee', compute = "_compute_sale_employee_ids")
    
    @api.onchange("user_employee_id")
    def _onchange_user_employee_id(self):
        if self.user_employee_id.user_id:
            self.user_id = self.user_employee_id.user_id

    @api.onchange("requestor_emp_employee")
    def _onchange_requestor_emp_employee(self):
        if self.requestor_emp_employee.user_id:
            self.requestor_emp = self.requestor_emp_employee.user_id

    def _force_confirm_warehouse(self):
        self.warehouse_status = 'confirmed'
        self.inventory_status = 'progress'
        self.user_confirm_warehouse_id = self.env.user.id
        self.user_confirm_warehouse_employee_id = self.search_employee()
        self.confirmed_warehouse_date = datetime.now()
        for m in self.move_lines:
            m.user_confirm_warehouse_id = self.env.user.id
            m.user_confirm_warehouse_employee_id = self.search_employee()
            m.confirmed_warehouse_date = datetime.now()
            if m.qty_counted > 0:
                m.auto_fill_done()
            else:
                for move_line in m.move_line_ids:
                    move_line.qty_done = 0

    def action_confirm_warehouse(self):
        for picking in self:
            if any(move.qty_counted > move.reserved_availability for move in picking.move_ids_without_package):
                raise UserError(_("สินค้ามีไม่เพียงพอ"))

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

    def _force_confirm_warehouse_out(self):
        self.warehouse_status = 'confirmed'
        self.inventory_status = 'progress'
        self.user_warehouse_out_id = self.env.user.id
        self.user_warehouse_out_employee_id = self.search_employee()
        self.warehouse_out_date = datetime.now()
        for m in self.move_lines:
            if m.transfers_qty > 0:
                m.auto_fill_done()
            else:
                for move_line in m.move_line_ids:
                    move_line.qty_done = 0

    def action_confirm_warehouse_out(self):
        for picking in self:
            if any(move.transfers_qty > move.reserved_availability for move in picking.move_ids_without_package):
                raise UserError(_("สินค้ามีไม่เพียงพอ"))

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
                record.validate_user_employee_id = record.search_employee()
                record.validate_date = datetime.now()
                if record.type_of_operation == 'internal':
                    record.user_warehouse_in_id = record.env.user.id
                    record.user_warehouse_in_employee_id = record.search_employee()
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
                rec.validate_user_employee_id = rec.search_employee()
                rec.validate_date = datetime.now()
                if rec.type_of_operation == 'internal':
                    rec.user_warehouse_in_id = rec.env.user.id
                    rec.user_warehouse_in_employee_id = rec.search_employee()
                    rec.warehouse_in_date = datetime.now()
        return res
    
    #--------------แก้ของborrow------------------
    def _button_validation_borrow(self):
        res = super(Picking, self)._button_validation_borrow()
        if self.state in ['done','ready_delivery']:
            self.warehouse_status = 'done'
            self.inventory_status = 'done'
            self.validate_user_id = self.env.user.id
            self.validate_user_employee_id = self.search_employee()
            self.validate_date = datetime.now()
        return res

class StockMove(models.Model):
    _inherit = 'stock.move'

    user_confirm_warehouse_id = fields.Many2one('res.users',string='Confirmed Warehouse user',copy=False)
    user_confirm_warehouse_employee_id = fields.Many2one('hr.employee', string = 'Confirmed Warehouse',copy=False)