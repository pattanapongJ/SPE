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
from odoo.tools.misc import format_date

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_borrow = fields.Many2one('sale.order', string="Sale Borrow", store=True)
    is_deduct_borrow = fields.Boolean(string="Deduct Borrow",default=False, copy=False)

    def auto_return_pick_borrow_done(self):
        for rec in self:
            if rec.sale_borrow:
                borrow_picking_ids = rec.env["stock.picking"].search([("sale_borrow", "=", rec.sale_borrow.id),("is_deduct_borrow","=",False),('picking_type_id.code','=','outgoing'),('state','=','ready_delivery')])
                for pick in borrow_picking_ids:
                    pick.force_done()

    def auto_cancel_so_borrow(self):
        for rec in self:
            if rec.sale_borrow:
                not_return_all = 0
                for sale_line in rec.sale_borrow.order_line:
                    if sale_line.return_qty != sale_line.borrow_qty:
                        not_return_all += 1
                if not_return_all == 0:
                    cancel_reason_id = rec.env["sale.order.cancel.reason"].search([("is_borrow", "=", True)],limit=1)
                    rec.sale_borrow.write({'state': 'cancel'})
                    rec.sale_borrow.write({'cancel_reason_id': cancel_reason_id.id})
                    rec.auto_return_pick_borrow_done()

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for rec in self:
            if rec.sale_borrow:
                if rec.origin:
                    if "Return" in rec.origin or "การส่งคืนของ" in self.origin:
                        for move_line in rec.move_ids_without_package:
                            for sale_line in rec.sale_borrow.order_line:
                                if move_line.product_id == sale_line.product_id:
                                    sale_line.return_qty += move_line.quantity_done

                        rec.auto_cancel_so_borrow()
                        
        return res
    
    def force_done(self):
        res = super(StockPicking, self).force_done()
        # for move_line in self.move_ids_without_package:
        #     for sale_line in self.sale_borrow.order_line:
        #         if move_line.product_id == sale_line.product_id:
        #             sale_line.borrow_qty += move_line.quantity_done

        return res
    
    def set_sale_borrow_qty(self):
        for move_line in self.move_ids_without_package:
            for sale_line in self.sale_borrow.order_line:
                if move_line.product_id == sale_line.product_id:
                    sale_line.borrow_qty += move_line.quantity_done

    