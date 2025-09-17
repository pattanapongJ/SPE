# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class SourceSPE(models.Model):
    _name = 'source.spe'
    _description = 'Source SPE' # This is what appears in debug mode or model list

    origin = fields.Char(string='Origin')
    description = fields.Char(string='Description')
    country_ids = fields.Many2many(
        "res.country",
        string="Countries",
    )
    def name_get(self):
        result = []
        for record in self:
            rec_name = record.description
            result.append((record.id, rec_name))
        return result