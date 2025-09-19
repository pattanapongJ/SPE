# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class MultiStockScrap(models.Model):
    _name = 'multi.stock.scrap'
    _inherit = ['mail.thread']
    _order = 'id desc'
    _description = "multi scrap"

    def _get_default_scrap_location_id(self):
        company_id = self.env.context.get('default_company_id') or self.env.company.id
        return self.env['stock.location'].search([('scrap_location', '=', True), ('company_id', 'in', [company_id, False])], limit=1).id

    def _get_default_location_id(self):
        company_id = self.env.context.get('default_company_id') or self.env.company.id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id
        return None

    name = fields.Char(
            'Reference',  default=lambda self: _('New'),
            copy=False, readonly=True, required=True,
            states={'done': [('readonly', True)]})
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, states={'done': [('readonly', True)]})
    origin = fields.Char(string='Source Document')
    location_id = fields.Many2one('stock.location', 'Source Location',
        domain = "[('usage', 'in', ['internal', 'production']), ('company_id', 'in', [company_id, False])]", required = True,
        states = {'done': [('readonly', True)]}, default = _get_default_location_id, check_company = True)
    scrap_location_id = fields.Many2one('stock.location', 'Scrap Location', default = _get_default_scrap_location_id,
        domain = "[('scrap_location', '=', True), ('company_id', 'in', [company_id, False])]", required = True,
        states = {'done': [('readonly', True)]}, check_company = True)
    state = fields.Selection(selection = [("draft", "Waiting Scrap"),
                                          ("done", "Done"),
                                          ("cancel", "Cancel")],
                             string = "State",default = "draft", readonly = True, )
    scrap_line = fields.One2many('stock.scrap', 'multi_scrap_id', string = 'Product Lines', copy = False,auto_join = True)
    picking_id = fields.Many2one('stock.picking', 'Picking',check_company = True)
    partner_id = fields.Many2one("res.partner", string = "Receive From")
    user_id = fields.Many2one("res.users", string = "Responsible")
    scheduled_date = fields.Datetime(string = 'Scheduled Date', default=lambda self: fields.Datetime.now())

    warehouse_status = fields.Selection([('warehouse', 'Inprogress'),('done','Done'),('cancel','Cancelled')],
                                        default='warehouse', string='Warehouse Status',copy=False)
    confirmed_warehouse_date = fields.Datetime('Confirmed Warehouse Date',copy=False)
    user_confirm_warehouse_employee_id = fields.Many2one('hr.employee', string = 'Confirmed Warehouse',copy=False)
    
    inventory_status = fields.Selection([('waiting', 'Waiting Confirm'),('progress', 'In Progress'),('done','Done'),('cancel','Cancelled')],
                                        default='waiting', string='Inventory Status',copy=False)
    validate_date = fields.Datetime('Validate Inventory Date',copy=False)
    validate_user_employee_id = fields.Many2one('hr.employee', string = 'Validate Inventory',copy=False)
    hide_validate_btn = fields.Boolean(compute='_compute_hide_validate_btn', string='hide validate')

    remark = fields.Text(string="Remark", tracking=True,) 
    remark_report = fields.Text(string="Remark Report", tracking=True,) 
    
    @api.depends('warehouse_status','state')
    def _compute_hide_validate_btn(self):
        for rec in self:
            rec.hide_validate_btn = False
            if not (rec.state == "draft" and rec.warehouse_status == "done" and rec.inventory_status in ["waiting", "progress"]):
                rec.hide_validate_btn = True

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            vals['name'] = self.env['ir.sequence'].next_by_code('multi.stock.scrap', sequence_date=seq_date) or _('New')
        result = super(MultiStockScrap, self).create(vals)
        return result

    def action_validate(self):
        for line in self.scrap_line:
            line.action_validate()
            if line.state != "done":
                raise ValidationError(_('You plan to transfer %.2f %s of %s but you '
                                        'only have 0 %s available stock in %s location.' %(line.scrap_qty, line.product_id.name,
                                                                                           line.product_uom_id.name, line.product_uom_id.name
                                                                                            , line.location_id.complete_name)))
        self.state = "done"
        if self.state =='done':
            self.inventory_status = 'done'
            self.validate_user_employee_id = self.env.user.employee_id.id
            self.validate_date = datetime.now()
    
    def action_print(self):
        return self.env.ref('hdc_multi_scrap.multi_scrap_report_view').report_action(self)

    def action_confirm(self):
        self.state = "draft"

    def action_cancel(self):
        if self.state == "draft":
            self.state = "cancel"
            self.scrap_line.action_cancel()
            self.inventory_status = 'cancel'
            self.warehouse_status = 'cancel'

    def action_get_stock_move_lines(self):
        action = self.env['ir.actions.act_window']._for_xml_id('stock.stock_move_line_action')
        move_id = []
        for line in self.scrap_line:
            move_id.append(line.move_id.id)
        action['domain'] = [('move_id', 'in', move_id)]
        return action

    def unlink(self):
        self.scrap_line.unlink()
        return super(MultiStockScrap, self).unlink()
    
    @api.onchange('location_id')
    def _onchange_location_id(self):
        scrap_line = self.scrap_line
        for line in scrap_line:
            line.location_id = self.location_id.id
        pass

    def action_confirm_warehouse(self):
        if all(line.scrap_qty > 0 for line in self.scrap_line):
            self.warehouse_status = 'done'
            self.inventory_status = 'progress'
            self.user_confirm_warehouse_employee_id = self.env.user.employee_id.id
            self.confirmed_warehouse_date = datetime.now()
        else:
            raise UserError(_("Please check quantity."))

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    multi_scrap_id = fields.Many2one('multi.stock.scrap', string = 'Multi Scrap Reference', required = False, ondelete = 'cascade', index = True, copy = False)
    reason_scrap_id = fields.Many2one('reason.scrap', string = 'Reason Scrap')
    remark_note = fields.Text("Remark")

    state = fields.Selection(
        selection_add=[('done', 'Done'), ("cancel", "Cancel")],
        ondelete={"stock.scrap": "cascade"})

    def action_cancel(self):
        for rec in self:
            if rec.state == "draft":
                rec.state = "cancel"

    @api.onchange('product_id')
    def _onchange_multi_picking_id(self):
        # default ให้ แถมๆ
        if self.multi_scrap_id:
            self.location_id = self.multi_scrap_id.location_id.id

    def _prepare_move_values(self):
        self.ensure_one()
        values = super(StockScrap, self)._prepare_move_values()
        if self.multi_scrap_id:
            values['name'] = self.multi_scrap_id.name
        return values

class Picking(models.Model):
    _inherit = "stock.picking"

    has_multi_scrap_move = fields.Boolean('Has Multi Scrap Moves', compute = '_has_multi_scrap_move')

    def _has_multi_scrap_move(self):
        for picking in self:
            # TDE FIXME: better implementation
            picking.has_multi_scrap_move = bool(self.env['multi.stock.scrap'].search_count([('picking_id', '=', picking.id)]))

    def action_see_move_multi_scrap(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("hdc_multi_scrap.action_multi_stock_scrap")
        scraps = self.env['multi.stock.scrap'].search([('picking_id', '=', self.id)])
        action['domain'] = [('id', 'in', scraps.ids)]
        action['context'] = dict(self._context, create = False)
        return action

    def button_multi_scrap(self):
        self.ensure_one()
        view = self.env.ref('hdc_multi_scrap.multi_stock_scrap_form_view2')
        products = self.env['product.product']
        scrap_line = []
        for move in self.move_ids_without_package:
            if move.state not in ('draft', 'cancel') and move.product_id.type in ('product', 'consu'):
                products |= move.product_id
                scrap_line.append([0,0, {
                    "product_id": move.product_id.id,
                    "product_uom_id": move.product_uom.id
                    }])
        return {
            'name': _('Multi Scrap Orders'),
            'view_mode': 'form',
            'res_model': 'multi.stock.scrap',
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'context': {
                'default_origin': self.name, 'default_picking_id': self.id,
                'default_partner_id': self.partner_id.id, 'default_user_id': self.user_id.id,
                'default_company_id': self.company_id.id, 'default_scrap_line': scrap_line,
                }, 'target': 'new',
            }



class ReasonScrap(models.Model):
    _name = 'reason.scrap'
    _description = "Reason Scrap"

    name = fields.Char('Reference', required = True)