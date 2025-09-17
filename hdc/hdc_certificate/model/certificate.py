# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class CertificatePurchase(models.Model):
    _inherit = "purchase.order"

    certificate_id = fields.Many2one('certificate.origin',string='Certificate Of Origin',copy=False)

class CertificateResPartner(models.Model):
    _inherit = "res.partner"

    certificate_id = fields.Many2one('certificate.origin',string='Certificate Of Origin',copy=False)
    payment_method = fields.Many2one(
        'account.payment.method', 
        string="Payment Method",
        domain="[('payment_type', '=', 'outbound')]",
    )

class CertificateOrigin(models.Model):
    _name = "certificate.origin"
    _description = "Certificate Of Origin"

    code = fields.Text(translate=True,required=True)
    name = fields.Char(translate=True)
    description = fields.Text(translate=True)

    def name_get(self):
        result = []
        for record in self:
            # ตรวจสอบว่ามีค่าทั้ง name และ code
            rec_name = f"{record.name} ({record.code})" if record.code else record.name
            result.append((record.id, rec_name))
        return result
