# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import re

class Quotations(models.Model):
    _inherit = 'quotation.order'

    incoterm_id = fields.Many2one(comodel_name="account.incoterms", string="Incoterm")

    @api.onchange('partner_id')
    def onchange_partner_id_incoterm_id(self):
        values = { }
        self.incoterm_id = False
        if self.partner_id.sale_incoterm_id:
            values['incoterm_id'] = self.partner_id.sale_incoterm_id
        self.update(values)
    