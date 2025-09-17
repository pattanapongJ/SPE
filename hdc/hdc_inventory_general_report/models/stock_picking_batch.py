from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
    


class PickingBatchInherit(models.Model):
    _inherit = 'stock.picking.batch'

    def do_batch_print_picking(self):
        return self.env.ref('hdc_inventory_general_report.batch_tranfer_report_view').report_action(self)
    