# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResCurrency(models.Model):
    _inherit = 'res.currency'
    
    
    show_in_purchase = fields.Boolean(string=_('Show In Purchase'), default=True)
    show_in_sale = fields.Boolean(string=_('Show In Sale'), default=True)
