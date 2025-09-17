# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from collections import defaultdict
import re

class BlanketOrder(models.Model):
    _inherit = "sale.blanket.order"
    
    @api.onchange("team_id")
    def _onchange_team_id_sale_team_addon(self):
        domain_sale_spec = [('id', 'in', self.team_id.sale_spec_member_ids.ids)]
        return {'domain': {'sale_spec':domain_sale_spec}}
    