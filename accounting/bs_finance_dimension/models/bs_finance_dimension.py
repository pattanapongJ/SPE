# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BsFinanceDimension(models.Model):
    _name = 'bs.finance.dimension'
    _description = 'Bs Finance Dimension'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin']

    name = fields.Char('Name', required=True, tracking=True)
    group_id = fields.Many2one(
        comodel_name='bs.dimension.group',
        string='Dimension',
        required=True, ondelete='restrict', tracking=True, readonly=True)
    
    type_id = fields.Many2one('bs.dimension.type',string="Type",ondelete='restrict',company_dependent=True)
    reference = fields.Char(string='Reference')

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        index=True)




