# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from datetime import datetime

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    source_spe = fields.Many2one('source.spe', string="Source")

    def write(self, vals):
        if "source_spe" in vals:
            for record in self:
                old_source = record.source_spe
                new_source = self.env['source.spe'].browse(vals["source_spe"])

                from_ids = old_source.country_ids.ids if old_source else []
                to_ids = new_source.country_ids.ids if new_source else []


        return super().write(vals)


