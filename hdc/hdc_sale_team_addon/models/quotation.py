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

    @api.onchange("team_id")
    def _onchange_team_id_sale_team_addon(self):
        domain_sale_spec = [('id', 'in', self.team_id.sale_spec_member_ids.ids)]
        return {'domain': {'sale_spec':domain_sale_spec}}