# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class ShCostCenter(models.Model):
    _name = 'sh.cost.center'
    _description = "Cost Centers"
    _rec_name = 'sh_code'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'resource.mixin']

    @api.model
    def default_company_id(self):
        return self.env.company

    sh_code = fields.Char(
        'Code',
        tracking=True,
        required=True
    )
    sh_title = fields.Char(
        'Title',
        tracking=True,
        required=True
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=default_company_id,
        tracking=True
    )
