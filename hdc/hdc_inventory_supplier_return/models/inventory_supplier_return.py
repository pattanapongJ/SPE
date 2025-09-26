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


class StockMoveInherit(models.Model):
    _inherit = "stock.move"

class StockPicking(models.Model):

    _inherit = 'stock.picking'
    
    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', 'กรุณาตรวจสอบ Sequence เนื่องจากอาจจะระบุผิดพลาด กรุณาติดต่อผู้ดูแลระบบ!'),
    ]
    

    supplier_return = fields.Boolean(string="Supplier Return Type",default=False)


    @api.onchange('picking_type_id')
    def _default_external_tranfer_type(self):
        res = super(StockPicking, self)._default_external_tranfer_type()
        self.supplier_return == False
        self.check_all == False
        if self.picking_type_id:
            addition_operation_type = self.env['stock.picking.type'].browse(
                self.picking_type_id.id).addition_operation_types
            if addition_operation_type:
                if addition_operation_type.code == "AO-09":
                    self.supplier_return = True
                else:
                    self.supplier_return = False
            else:
                self.supplier_return = False
                self.check_all = False
        else:
            self.supplier_return = False
            self.check_all = False
        if self.supplier_return:
            self.check_all = True