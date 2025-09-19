from odoo import fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    is_head_office = fields.Boolean(string="Head Office")