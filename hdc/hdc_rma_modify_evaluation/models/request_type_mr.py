from odoo import fields, models, api

class RequestTypeMR(models.Model):
    _inherit = "request.type.mr"

    is_repair = fields.Boolean(string='Is Repair')