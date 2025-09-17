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

    order_id = fields.Many2one('sale.order',string='Ref Document')
    customer_po = fields.Char(string='PO Customer')
    remark = fields.Text(string='Remark')
    project_name = fields.Char(string='Project Name')

    @api.onchange('order_id')
    def order_id_change(self):
        self.customer_po = self.order_id.customer_po
        self.remark = self.order_id.remark
        self.project_name = self.order_id.project_name.project_name
        move_ids_without_package_data_list = []
        if self.addition_operation_types.code == "AO-06":
            self.move_ids_without_package = False
            for rec in self.order_id.order_line:
                if rec.product_id.type != "service":
                    data_rec = (0,0,{
                    "product_id":rec.product_id.id,
                    "name":rec.product_id.display_name,
                    "description_picking":rec.product_id.name,
                    "location_id":self.picking_type_id.default_location_src_id.id,
                    "location_dest_id":self.picking_type_id.default_location_dest_id.id,
                    "product_uom_qty":rec.product_uom_qty,
                    "product_uom":rec.product_uom.id,
                    })
                    move_ids_without_package_data_list.append(data_rec)
            self.update({   
                 'move_ids_without_package': move_ids_without_package_data_list,
                })

   
        

    