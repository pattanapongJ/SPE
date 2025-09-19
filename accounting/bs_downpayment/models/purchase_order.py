# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    
    bs_downpayment_id = fields.Many2one('bs.downpayment',string='Down Payment',copy=False)
