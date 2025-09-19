from odoo import api, fields, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    no_of_signature = fields.Integer('Number of Signature', copy=False,default=0)