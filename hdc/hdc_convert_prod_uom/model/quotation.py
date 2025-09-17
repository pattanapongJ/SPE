# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import re

class Quotations(models.Model):
    _inherit = 'quotation.order'

class QuotationLine(models.Model):
    _inherit = 'quotation.order.line'

    sale_uom_map_ids = fields.Many2many(related="product_id.sale_uom_map_ids")

    @api.onchange("product_id")
    def product_id_change(self):
        result = super().product_id_change()
        if self.product_id:
            product_uom = self.product_id.uom_map_ids.filtered(lambda l: l.is_default_sale == True).mapped("uom_id")
            if product_uom:
                self.product_uom = product_uom[0]
        domain_uom = [("id", "in", self.sale_uom_map_ids.ids)]
        if result and 'domain' in result:
            result['domain']['product_uom'] = domain_uom
        else:
            result = {"domain": {"product_uom": domain_uom}}
        return result
