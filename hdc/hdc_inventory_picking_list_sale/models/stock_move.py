# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from collections import defaultdict
from datetime import datetime
from itertools import groupby
from operator import itemgetter
from re import findall as regex_findall
from re import split as regex_split

from dateutil import relativedelta

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.float_utils import float_compare, float_is_zero, float_repr, float_round
from odoo.tools.misc import clean_context, format_date, OrderedSet

class StockMove(models.Model):
    _inherit = "stock.move"

    picking_list_line = fields.One2many('picking.lists.line', 'move_id', string = "Picking Lists line", copy = False)
    picking_done_qty = fields.Float("Picking Done QTY", digits = 'Product Unit of Measure',
                                    index=True, compute="_compute_picking_done_qty")
    is_done_picking = fields.Boolean(compute="_compute_picking_done_qty",
                                     string="is done picking",index=True, store=True)


    def _compute_picking_done_qty(self):
        for rec in self:
            if rec.picking_list_line:
                state_done = rec.picking_list_line.filtered(lambda l: l.state != "cancel")
                rec.picking_done_qty = sum(state_done.mapped('qty'))
            else:
                rec.picking_done_qty = 0.0
            if rec.picking_done_qty >= rec.product_uom_qty:
                rec.is_done_picking = True
            else:
                rec.is_done_picking = False


class AccountInvoice(models.Model):
    _inherit = "account.move"

    picking_list = fields.Many2many('picking.lists', string = 'Picking List')

    def button_cancel(self):
        self.write({'auto_post': False, 'state': 'cancel'})
        # if self.picking_list:
        #     for line in self.picking_list:
        #         line.invoice_check = False