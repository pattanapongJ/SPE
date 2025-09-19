from email.policy import default
import json
import time
from ast import literal_eval
from collections import defaultdict
from datetime import date
from itertools import groupby
from operator import attrgetter, itemgetter
from collections import defaultdict
from datetime import datetime

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_datetime
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, format_date, OrderedSet


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    is_repair_type_id = fields.Boolean(related='order_id.type_id.is_repair',string='Is Repair Sales Types')
    product_type_mr = fields.Many2one('product.type.mr', string='Product Type',tracking=True,index=True,)
    request_type_mr = fields.Many2one('request.type.mr', string='Request Type', required=False, tracking=True, index=True)

    def create_mrp_request(self):
        if self.is_repair_type_id:
            move_raw_ids = []
            repair_product_line_ids = []
            if self.move_lines:
                for item in self.move_lines:
                    move_raw_ids.append([0, 0, {
                        "product_id": item.product_id.id,
                        "uom_id": item.product_uom.id,
                        "demand_qty": item.product_uom_qty,}])
            if self.order_id.repair_order_ids:
                if len(self.order_id.repair_order_ids) == 1:
                    for item in self.order_id.repair_order_ids.operations:
                        repair_product_line_ids.append([0, 0, {
                            "type":item.type,
                            "product_id": item.product_id.id,
                            "name":item.name,
                            "product_uom_qty": item.product_uom_qty,
                            "product_uom": item.product_uom.id,}])
            
            request_type = self.request_type_mr
            if request_type:
                mr_id = self.env['mrp.mr'].create({
                    'request_type': request_type.id,
                    'partner_id': self.partner_id.id,
                    'product_type': self.product_type_mr.id,
                    'department_id': self.product_type_mr.department_id.id,
                    'sale_order_id': self.order_id.id,
                    'ref_no':self.name,
                    'product_line_ids': move_raw_ids,
                    'is_repair':self.is_repair_type_id,
                    'repair_product_line_ids':repair_product_line_ids,
                    'picking_type_id':self.product_type_mr.picking_type_id.id,
                    'picking_type_do_id':self.product_type_mr.out_factory_picking_type_id.id,
                })         

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for inter in self:
            if inter.batch_id:
                continue
                
            if inter.state == "done":
                inter_pick_ids = self.env['stock.picking'].search([('name', '=', inter.origin)], limit=1)
                picking_in_type_id = self.env['stock.picking'].search([('origin', '=', inter_pick_ids.name), ('state', 'not in', ('done', 'cancel')), (
                'picking_type_id', '=', inter_pick_ids.from_warehouse.inter_transfer_receive.id)])

                picking_out_type_id = self.env['stock.picking'].search(
                    [('origin', '=', inter_pick_ids.name), ('state', '=', 'done'),
                    ('picking_type_id', '=', inter_pick_ids.to_warehouse.inter_transfer_delivery.id)])
                
                if not picking_in_type_id and picking_out_type_id:
                    inter_pick_ids.inter_state = 'done'
                    inter_pick_ids.state = 'done'
                    if inter_pick_ids.inter_state == 'done':
                        inter_pick_ids.create_mrp_request()
        if inter.claim_id.rma_type == 'receive_modify':
            inter.claim_id.set_claim_modify_line_ids_serial_lot_ids()
                                                          
        return res
    
class PickingType(models.Model):
    _inherit = "stock.picking.type"

    is_factory = fields.Boolean(string='Is Factory')