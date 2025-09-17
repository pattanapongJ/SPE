# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    
    bs_downpayment_id = fields.Many2one('bs.downpayment',string='Down Payment',copy=False)
    
    
    
    
