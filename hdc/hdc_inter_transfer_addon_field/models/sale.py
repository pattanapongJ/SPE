from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

from werkzeug.urls import url_encode

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    inter_transfer_num = fields.Integer(string='Number of Inter Transfer',compute='_compute_inter_transfer_num',default=0)

    def _compute_inter_transfer_num(self):
        for line in self:
            inter_transfer_count = self.env['stock.picking'].search_count([('addition_operation_types.code', '=',"AO-06"),('order_id', '=',line.id)]) 
            line.update({   
                 'inter_transfer_num': inter_transfer_count,
                })                
            
    def create_inter_transfer(self):
        context = {}
        picking_type = self.env['stock.picking.type'].search([('addition_operation_types.code', '=',"AO-06"),('warehouse_id','=',self.warehouse_id.id)])
        context.update({
            'default_order_id' :self.id,
            'default_picking_type_id' :picking_type.id,
            })
        return {
                'type': 'ir.actions.act_window',
                'name': 'Create Inter Transfer',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'target': 'current',
                'context': context,
            }
    def action_view_inter_transfer_detail(self):   
        picking_ids = self.env['stock.picking'].search([('addition_operation_types.code', '=',"AO-06"),('order_id', '=',self.id)]) 
        if len(picking_ids) == 1:
            return {
                "name": _("รายละเอียด"),
                "view_mode": "form",
                "res_model": "stock.picking",
                "type": "ir.actions.act_window",
                'res_id': picking_ids.id,
                "flags": {"initial_mode": "view"},                
                }
        else:            
            return {
                "name": _("รายละเอียด"),
                "view_mode": "tree,form",
                "res_model": "stock.picking",
                "type": "ir.actions.act_window",
                "domain": [("id", "in", picking_ids.ids)],                
                }