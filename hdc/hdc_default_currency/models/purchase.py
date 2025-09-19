from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from functools import partial
from itertools import groupby
import re
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # @api.onchange('partner_id', 'company_id')
    # def onchange_partner_id(self):
    #     # Ensures all properties and fiscal positions
    #     # are taken with the company of the order
    #     # if not defined, with_company doesn't change anything.
    #     self = self.with_company(self.company_id)
    #     if not self.partner_id:
    #         self.fiscal_position_id = False

    #         # self.currency_id = self.env.company.currency_id.id

    #         currency_id = self.env['ir.config_parameter'].sudo().get_param('account_purchase_currency_res_setting')
    #         cur_id = self.env['res.currency'].browse(currency_id)

    #         self.currency_id = int(cur_id.id)

    #     else:
    #         self.fiscal_position_id = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id)
    #         self.payment_term_id = self.partner_id.property_supplier_payment_term_id.id
    #         self.currency_id = self.partner_id.property_purchase_currency_id.id or self.env.company.currency_id.id
    #     return {}

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    currency_id = fields.Many2one('res.currency', 'Currency', required = True, domain="[('rate_type', '=', 'sell'), ('active', '=', True)]")


    # @api.model
    # def _default_currency(self):
    #     currency_id = self.env['ir.config_parameter'].sudo().get_param('account_purchase_currency_res_setting')

    #     return int(currency_id)
