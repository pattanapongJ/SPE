# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class BsFinanceDimension(models.Model):
    _inherit = 'bs.finance.dimension'

    res_id = fields.Integer(string='Resource ID')
    active = fields.Boolean('Active', default=True)
    

    
    
