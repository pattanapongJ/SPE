from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    fax = fields.Char()

class ResCompany(models.Model):
    _inherit = "res.company"

    fax = fields.Char()
    branch = fields.Char(related="partner_id.branch", string="Tax Branch", readonly=False)
