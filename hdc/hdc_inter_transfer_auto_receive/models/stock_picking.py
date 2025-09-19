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



class StockPickingInherit(models.Model):

    _inherit = 'stock.picking'

    def approve(self):
        auto_receive = self.picking_type_id.auto_receive
        code = self.picking_type_id.addition_operation_types.code #== "AO-06":
        if auto_receive:
            if code == "AO-06":
                if self.to_warehouse:
                    # OUTGOING ------------
                    move_line = []
                    if self.to_warehouse.inter_transfer_delivery :
                    # if self.to_warehouse.out_type_id:
                        for move in self.move_lines:
                            move_line.append((0, 0, {
                                "product_id": move.product_id.id,
                                "name": move.name,
                                "product_uom_qty": move.product_uom_qty,
                                "qty_counted": move.product_uom_qty,
                                "product_uom": move.product_uom.id,
                                "company_id": move.company_id.id,
                                "location_id": move.location_dest_id.id,
                                "location_dest_id": move.location_id.id,
                                "remark": move.remark,
                                }))

                        picking_out = self.env["stock.picking"].create({
                            "picking_type_id": self.to_warehouse.inter_transfer_delivery.id if self.to_warehouse.inter_transfer_delivery else  self.to_warehouse.out_type_id.id,
                            "origin": self.name,
                            "partner_id": self.partner_id.id,
                            "location_id": self.transit_location.id,
                            "location_dest_id": self.location_dest_id.id,
                            "move_lines": move_line,
                            "remark": self.remark,
                            "note": self.note,
                            })
                        
                        picking_out.action_confirm()
                        picking_out.action_assign()
                        for line in picking_out.move_ids_without_package.move_line_ids:
                            line.qty_done = line.product_uom_qty
                        picking_out.action_confirm_warehouse()
                        picking_out.with_context(skip_immediate=True,skip_backorder=True).button_validate()
                    else:
                        raise ValidationError(_("Not Out Type in Warehouse"))

                    move_line = []
                    # INCOMING ------------
                    if self.from_warehouse.in_type_id:
                        for move in self.move_lines:
                            move_line.append((0, 0, {
                                "product_id": move.product_id.id,
                                "name": move.name,
                                "product_uom_qty": move.product_uom_qty,
                                "product_uom": move.product_uom.id,
                                "company_id": move.company_id.id,
                                "location_id": self.transit_location.id,
                                "location_dest_id": self.location_dest_id.id,
                                "remark": move.remark,
                                }))

                        picking_in = self.env["stock.picking"].create({
                            "picking_type_id": self.from_warehouse.inter_transfer_receive.id if self.from_warehouse.inter_transfer_receive else self.from_warehouse.in_type_id.id,
                            "origin": self.name,
                            "partner_id": self.partner_id.id,
                            "location_id": self.location_dest_id.id,
                            "location_dest_id": self.location_id.id,
                            "move_lines": move_line,
                            "remark": self.remark,
                            "note": self.note,
                            })
                        picking_in.action_confirm()
                    else:
                        raise ValidationError(_("Not In Type in Warehouse"))

                    self.inter_state = "delivery"
                    self.approve_inter = self.env.user.id
        else:
            res = super(StockPickingInherit, self).approve()
            return res
        


class StockPickingTypeInherit(models.Model):

    _inherit = 'stock.picking.type'

    auto_receive = fields.Boolean(default=False)
