from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
import re

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from dateutil.relativedelta import relativedelta

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder,self).onchange_partner_id()
        self.delivery_trl = self.partner_id.delivery_trl.id if self.partner_id.delivery_trl else False
        self.delivery_trl_description = self.partner_id.delivery_trl_description or False
        self.delivery_company = self.partner_id.delivery_company.id if self.partner_id.delivery_company else False
        self.delivery_company_description = self.partner_id.delivery_company_description or False
        self._onchange_pricelist_to_change_fiscal_position_id()