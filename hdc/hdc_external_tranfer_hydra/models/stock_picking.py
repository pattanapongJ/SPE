from email.policy import default
import json
from ast import literal_eval
from datetime import datetime, time
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_repr, float_round
from odoo.tools.misc import clean_context, format_date, OrderedSet

class PickingType(models.Model):
    _inherit = "stock.picking.type"

    def _get_action(self, action_xmlid):
        action = self.env["ir.actions.actions"]._for_xml_id(action_xmlid)
        if self:
            action['display_name'] = self.display_name

        default_immediate_tranfer = False
        if self.env['ir.config_parameter'].sudo().get_param('stock.no_default_immediate_tranfer'):
            default_immediate_tranfer = False

        context = {
            'search_default_picking_type_id': [self.id],
            'default_picking_type_id': self.id,
            'default_immediate_transfer': default_immediate_tranfer,
            'default_company_id': self.company_id.id,
        }

        action_context = literal_eval(action['context'])
        context = {**action_context, **context}
        action['context'] = context
        return action

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.onchange('picking_type_id')
    def _default_external_tranfer_type(self):
        self.external_tranfer_types == False
        self.check_all == False
        if self.picking_type_id:
            addition_operation_type = self.env['stock.picking.type'].browse(
                self.picking_type_id.id).addition_operation_types
            if addition_operation_type:
                if addition_operation_type.code == "AO-01":
                    self.external_tranfer_types = True
                else:
                    self.external_tranfer_types = False
            else:
                self.external_tranfer_types = False
                self.check_all = False
        else:
            self.external_tranfer_types = False
            self.check_all = False
        if self.external_tranfer_types:
            self.check_all = True
    check_all = fields.Boolean(string="Check All", default=False)
    external_tranfer_types = fields.Boolean(string="External Tranfer Types",default=False)
    employee_name = fields.Many2one("res.users", string="Requestor Name", default=lambda self: self.env.user)
    department_id = fields.Many2one("hr.department", string="Department", related="employee_name.department_id")
    approved_reviewer = fields.Many2one('res.users', 'Reviewer',default=lambda self: self.env.user)
    approved = fields.Many2one('res.users', string="Approver",default=lambda self: self.env.user)
    schedule_req = fields.Date(string="Schedule Date Req",default=datetime.now())

    expense_count = fields.Integer(compute='compute_expense_count')
    def get_expense(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Expenses to Report',
            'view_mode': 'tree,form',
            'res_model': 'hr.expense',
            'domain': [('requisition_id', '=', self.id)],
            'context': "{'create': False}"
        }
    def compute_expense_count(self):
        for record in self:
            record.expense_count = self.env['hr.expense'].search_count(
                [('requisition_id', '=', self.id)])