# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
import re

class Company(models.Model):
    _inherit = "res.company"

    billing_remark_th = fields.Text("Billing Remark")
    billing_remark_en = fields.Text("Billing Remark")