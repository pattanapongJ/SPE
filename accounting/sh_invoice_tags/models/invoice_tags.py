# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models


class ShInvoiceTags(models.Model):
    _name = 'sh.invoice.tags'
    _description = 'Invoice Tags'

    name = fields.Char('Tag Name', required=True, translate=True)
    color = fields.Integer('Color Index', default=1)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]
    
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
