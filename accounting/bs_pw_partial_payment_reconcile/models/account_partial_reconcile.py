# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'
    
    
    reconcile_date = fields.Date(string='Reconcile Date',copy=False)
