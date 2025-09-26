# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
import re

class Company(models.Model):
    _inherit = "res.company"

    sale_contact_id = fields.Many2one('res.partner', string='Sale Contact')