# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
import re

class Company(models.Model):
    _inherit = "res.company"

    street = fields.Char(compute='_compute_address', inverse='_inverse_street', required=True)
    street2 = fields.Char(compute='_compute_address', inverse='_inverse_street2', required=True)
    zip = fields.Char(compute='_compute_address', inverse='_inverse_zip', size=5, required=True)
    vat = fields.Char(related='partner_id.vat', string="Tax ID", readonly=False, size=13, required=True)
    branch_number = fields.Char(string='Branch Number', size=5, required=True)
    branch_name = fields.Char(string='Branch Name', required=True)
    line = fields.Char(string='Line')
    facebook = fields.Char(string='Facebook')
    date_logo = fields.Datetime()
    active = fields.Boolean(default=True)
    fax = fields.Char()
    mobile = fields.Char(size=10)

    ############# TH ############
    name_th = fields.Char(string='Name TH', required=True)
    street_th = fields.Char(string='Street', required=True)
    street2_th = fields.Char(string='Street2', required=True)
    city_th = fields.Char(string='City')
    state_th_id = fields.Many2one(
        'res.country.state', compute='_compute_address', inverse='_inverse_state',
        string="Fed. State", domain="[('country_id', '=?', country_th_id)]"
    )
    zip_th = fields.Char(string='Zip', required=True)
    country_th_id = fields.Many2one('res.country', string="Country")
    email_th = fields.Char(string='Email')
    phone_th = fields.Char(string='Phone')
    fax_th = fields.Char(string='Fax')
    mobile_th = fields.Char(string='Mobile')
    line_th = fields.Char(string='Line')
    vat_th = fields.Char(string='Tax ID', required=True)
    branch_number_th = fields.Char(string='Branch Number', required=True)
    branch_name_th = fields.Char(string='Branch Name', required=True)
    company_registry_th = fields.Char(string='Company Registry')
    website_th = fields.Char('Website')
    facebook_th = fields.Char(string='Facebook')
    report_header_th = fields.Binary(string="Report Header", attachment=True, tracking=True)
    report_header_eng = fields.Binary(string="Report Header ENG", attachment=True, tracking=True)


    # @api.constrains('fax')
    # def _check_fax(self):
    #     for company in self:
    #         # rule = re.compile(r'^(?:\+?44)?[07]\d{9,13}$')
    #         rule = re.compile(r'\(?(\d{2})\)?[ -.]?(\d{3})[ -.]?(\d{4})')
    #         if not rule.search(company.fax):
    #             msg = u"Invalid Fax number."
    #             raise ValidationError(msg)

