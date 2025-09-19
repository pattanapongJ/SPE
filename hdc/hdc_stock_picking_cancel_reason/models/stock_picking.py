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
    _inherit = "stock.picking"

    cancel_reason_id = fields.Many2one(
        comodel_name="stock.picking.cancel.reason",
        string="Reason for cancellation",
        readonly=True,
        ondelete="restrict",
    )
    cancel_description = fields.Text(string="Description for cancellation", readonly=True)

    state_before_cancel = fields.Char("state before cancel")

    state = fields.Selection(selection_add = [("waiting_cancel", "Waiting for cancel"),("skip_done", "Skip For Cancel"), ("done",)], )

    def reject_cancel(self):
        self.state = self.state_before_cancel
        self.sale_id.state = 'sale'

class StockPickingCancelReason(models.Model):
    _name = "stock.picking.cancel.reason"
    _description = "Stock Picking Cancel Reason"

    name = fields.Char(string="Reason", required=True, translate=True)
    active = fields.Boolean(default=True)

class StockMove(models.Model):
    _inherit = 'stock.move'

    state = fields.Selection(selection_add = [("waiting_cancel", "Waiting for cancel"),("skip_done", "Skip For Cancel"), ("done",)], )

