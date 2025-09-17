# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from lxml import etree

_logger = logging.getLogger(__name__)


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'
    
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ProductPricelist, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                         submenu=submenu)
        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='currency_id']"):
            if view_type == 'form':
                node.set('domain',"[('show_in_sale', '=', True)]")
        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res
