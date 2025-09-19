# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.tools import float_round
from odoo.exceptions import UserError


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    is_modify = fields.Boolean(string='Is Modify')