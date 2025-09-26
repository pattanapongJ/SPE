# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResBranch(models.Model):
    _inherit = 'res.branch'

    address_eng = fields.Text('Address Eng')
    fax = fields.Char(string='Fax No')
    branch_number = fields.Char(string='Branch Number',required=True)
    is_head_office = fields.Boolean(string='Head Office')
