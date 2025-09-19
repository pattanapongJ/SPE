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
    _description = "Quotations Order"

    @api.onchange('pricelist_id')
    def _onchange_pricelist_to_change_fiscal_position_id(self):
        self.currency_id = self.pricelist_id.currency_id.id
        fiscal_position_ids = self.env.company.fiscal_position_id
        fiscal_position = False
        if len(fiscal_position_ids) > 0:
            for quotation in self:
                for fiscal in fiscal_position_ids:
                    for tax_ids in fiscal.tax_ids:
                        if tax_ids.tax_dest_id.price_include == True:
                            fiscal_position = fiscal
                            break
                    if fiscal_position != False:
                        break
                if fiscal_position == False:
                    fiscal_position = fiscal_position_ids[0]
                quotation.fiscal_position_id = fiscal_position
        if fiscal_position == False:
            if self.quotation_line and self.pricelist_id and self._origin.pricelist_id != self.pricelist_id:
                self.show_update_pricelist = True
            else:
                self.show_update_pricelist = False
            for order in self:
                fiscal_position_id = order.pricelist_id.fiscal_position_id
                if fiscal_position_id:
                    order.fiscal_position_id = fiscal_position_id
        
        self.onchange_partner_shipping_id()

    @api.onchange('partner_shipping_id', 'partner_id', 'company_id')
    def onchange_partner_shipping_id(self):
        fiscal_position_ids = self.env.company.fiscal_position_id
        fiscal_position = False
        if len(fiscal_position_ids) > 0:
            for order in self:
                for fiscal in fiscal_position_ids:
                    for tax_ids in fiscal.tax_ids:
                        if tax_ids.tax_dest_id.price_include == True:
                            fiscal_position = fiscal
                            break
                    if fiscal_position != False:
                        break
                if fiscal_position == False:
                    fiscal_position = fiscal_position_ids[0]
                order.fiscal_position_id = fiscal_position
        
        if self.partner_id.property_account_position_id:
            customer_fiscal_position_id = self.env['account.fiscal.position'].with_company(self.company_id).get_fiscal_position(self.partner_id.id, self.partner_shipping_id.id)
        else:
            customer_fiscal_position_id = False

        if customer_fiscal_position_id:
            if customer_fiscal_position_id.id != self.fiscal_position_id.id:
                self.fiscal_position_id = customer_fiscal_position_id.id
        return {}