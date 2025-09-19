# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    is_downpayment = fields.Boolean(string=_('Is Down Payment?'), default=False,copy=True)

    @api.onchange('is_downpayment')
    def onchange_is_downpayment(self):
        if self.is_downpayment:
            self.type ='service'
