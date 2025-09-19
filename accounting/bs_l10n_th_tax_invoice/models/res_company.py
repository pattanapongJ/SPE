from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    allow_defer_posting = fields.Boolean(string='Allow deferred posting', default=False, copy=False)
