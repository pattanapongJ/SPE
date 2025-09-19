from odoo import api, fields, models, _


class ResBranch(models.Model):
    _inherit = 'res.branch'

    fax_no = fields.Char(string='Fax No',stored=True)
    address_en = fields.Char(string='Address Eng',stored=True)
    name = fields.Char(string='Branch Name',required=True)
    name_en = fields.Char(string='Branch Name Eng',required=True,stored=True)
    branch_no = fields.Char(string='Branch No',required=True,stored=True)