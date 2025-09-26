from odoo import fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    name_eng = fields.Char(string="Name Eng")

    purchase_team = fields.Many2one("purchase.team", string="Purchase Team")
    shipping = fields.Char(string="Shipping")
