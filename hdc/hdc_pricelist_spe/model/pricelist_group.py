# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class PricelistGroups(models.Model):
    _name = "pricelist.groups"
    _description = "Pricelist Groups"

    name = fields.Char(string='Group Name',index=True,required=True)
    active = fields.Boolean(string="Status", default=True)

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            if self.search([('name', '=', record.name), ('id', '!=', record.id)]):
                raise ValidationError("Group Name must be unique!")
    


