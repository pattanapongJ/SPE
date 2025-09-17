# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from lxml import etree
from datetime import datetime, timedelta, date
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import re

class Quotations(models.Model):
    _name = 'quotation.order'
    _inherit = ['quotation.order','bs.base.finance.dimension']
    
    @api.onchange('finance_dimension_1_id')
    def onchange_finance_dimension_1_id(self):
        self.quotation_line.filtered(lambda x: not x.display_type).write({
            'finance_dimension_1_id': self.finance_dimension_1_id.id
        })

    @api.onchange('finance_dimension_2_id')
    def onchange_finance_dimension_2_id(self):
        self.quotation_line.filtered(lambda x: not x.display_type).write({
            'finance_dimension_2_id': self.finance_dimension_2_id.id
        })

    @api.onchange('finance_dimension_3_id')
    def onchange_finance_dimension_3_id(self):
        self.quotation_line.filtered(lambda x: not x.display_type).write({
            'finance_dimension_3_id': self.finance_dimension_3_id.id
        })

class QuotationLine(models.Model):
    _name = 'quotation.order.line'
    _inherit = ['quotation.order.line','bs.base.finance.dimension']
                
    @api.model
    def default_get(self, fields):
        rec = super(QuotationLine, self).default_get(fields)
        if self.quotation_id:
            self.update({
                'finance_dimension_1_id': self.finance_dimension_1_id or self.quotation_id.finance_dimension_1_id.id,
                'finance_dimension_2_id': self.finance_dimension_2_id or self.quotation_id.finance_dimension_2_id.id,
                'finance_dimension_3_id': self.finance_dimension_3_id or self.quotation_id.finance_dimension_3_id.id
            })

        return rec