# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools.misc import formatLang, get_lang
import re

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("team_id")
    def _onchange_team_id_sale_team_addon(self):
        domain_sale_spec = [('id', 'in', self.team_id.sale_spec_member_ids.ids)]
        return {'domain': {'sale_spec':domain_sale_spec}}