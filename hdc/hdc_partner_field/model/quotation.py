from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
import re

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang

class Quotations(models.Model):
    _inherit = 'quotation.order'

    remark_payment_term = fields.Text(string="Remark Payment Term")

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(Quotations,self).onchange_partner_id()
        self.delivery_trl = self.partner_id.delivery_trl.id if self.partner_id.delivery_trl else False
        self.delivery_trl_description = self.partner_id.delivery_trl_description or False
        self.delivery_company = self.partner_id.delivery_company.id if self.partner_id.delivery_company else False
        self.delivery_company_description = self.partner_id.delivery_company_description or False
        self.remark_payment_term = self.partner_id.internal_remark