from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _description = 'Sales Order'


    @api.onchange('partner_id')
    def _onchange_customer_global_discount_update(self):
        for order in self:
            if order.partner_id:
                if order.partner_id.global_discount:
                    order.global_discount = order.partner_id.global_discount


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _description = 'Sales Order Line'