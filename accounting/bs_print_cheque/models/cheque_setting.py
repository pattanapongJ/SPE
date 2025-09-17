# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ChequeSetting(models.Model):
    _inherit = 'cheque.setting'

    is_acc_pay = fields.Boolean('Crossed Cheque', default=True)
    crossed_text = fields.Char(string='Crossed Text')
