# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_channel = fields.Char("Sale Channel", required=False)
    is_customer = fields.Boolean('Type Is Customer', default=False)
    is_purchase = fields.Boolean('Type Is Purchase', default=False)
    street = fields.Char(required=True)
    street2 = fields.Char(required=True)
    vat = fields.Char(string='Tax ID', size=13, index=True, required=False, help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.")
    zip = fields.Char(change_default=True, size=5, required=True)
    phone = fields.Char(required=True)
    active = fields.Boolean(default=True)

    # ข้อมูลใบกำกับภาษี tax invoice
    customer_type = fields.Selection(selection=[('company', 'นิติบุคคล'),('person', 'บุคคลธรรมดา')],string="Customer Type")
    name_tax_invoice = fields.Char("Name")
    sale_channel_tax_invoice = fields.Char("Sale Channel")
    street_tax_invoice = fields.Char(string="Stree1")
    street2_tax_invoice = fields.Char(string="Stree2")
    zip_tax_invoice = fields.Char(string="Zip",size=5)
    vat_tax_invoice = fields.Char(string='Tax ID', size=13, index=True)
    phone_tax_invoice = fields.Char(string='Phone')
    email_tax_invoice = fields.Char(string='Email')
    branch_name = fields.Char('Branch Name')
    branch_number = fields.Char('Branch Number')
    billing_date = fields.Datetime(string='Billing Date')
    cheque_date = fields.Datetime(string='Cheque Date')
    last_update_image = fields.Date(string='Latest Update')

    @api.model
    def create(self, vals):
        if 'image_1920' in vals and vals['image_1920']:
            vals['last_update_image'] = fields.Datetime.now()
        res = super(ResPartner, self).create(vals)
        return res

    def write(self, values):
        if 'image_1920' in values and values.get('image_1920'):
            values['last_update_image'] = fields.Datetime.now()

        result = super(ResPartner, self).write(values)
        return result
