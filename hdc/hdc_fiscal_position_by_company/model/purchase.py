# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from itertools import groupby
from pytz import timezone, UTC
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang, format_amount


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _description = "Purchase Order"

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        # Ensures all properties and fiscal positions
        # are taken with the company of the order
        # if not defined, with_company doesn't change anything.
        self = self.with_company(self.company_id)
        if not self.partner_id:
            self.fiscal_position_id = False
            self.currency_id = self.env.company.currency_id.id
        else:
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
            if fiscal_position == False:
                self.fiscal_position_id = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id)
            self.payment_term_id = self.partner_id.property_supplier_payment_term_id.id
            self.currency_id = self.partner_id.property_purchase_currency_id.id or self.env.company.currency_id.id
        return {}

    