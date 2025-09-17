from email.policy import default
import json
from datetime import datetime, time
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    return_customer_types = fields.Boolean(string="Return Customer Types",default=False)
    return_type = fields.Char(string='Return Type')


    @api.onchange('picking_type_id')
    def _default_return_customer_type(self):
        res = super(StockPicking, self)._default_external_tranfer_type()
        self.return_customer_types == False
        self.check_all == False
        if self.picking_type_id:
            addition_operation_type = self.env['stock.picking.type'].browse(
                self.picking_type_id.id).addition_operation_types
            if addition_operation_type:
                if addition_operation_type.code == "AO-05":
                    self.return_customer_types = True
                else:
                    self.return_customer_types = False
            else:
                self.return_customer_types = False
                self.check_all = False
        else:
            self.return_customer_types = False
            self.check_all = False
        if self.return_customer_types:
            self.check_all = True

    repair_count = fields.Integer(compute='compute_repair_count')
    def get_repair(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Repair Orders',
            'view_mode': 'tree,form',
            'res_model': 'repair.order',
            'domain': [('requisition_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def compute_repair_count(self):
        for record in self:
            record.repair_count = self.env['repair.order'].search_count(
                [('requisition_id', '=', self.id)])

class stock_move(models.Model):
    _inherit = 'stock.move'
    return_uom_qty = fields.Float(related="product_uom_qty", string="Return QTY", readonly=False)