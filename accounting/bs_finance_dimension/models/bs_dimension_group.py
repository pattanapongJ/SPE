# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BsDimensionGroup(models.Model):
    _name = 'bs.dimension.group'
    _description = 'Dimension Group'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin']

    name = fields.Char('Name', copy=False, required=True, tracking=True)
    finance_dimension_ids = fields.One2many(
        comodel_name='bs.finance.dimension',
        inverse_name='group_id',
        string='Finance Dimension',
        required=False)

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Dimension Name Already Exist.')
    ]
