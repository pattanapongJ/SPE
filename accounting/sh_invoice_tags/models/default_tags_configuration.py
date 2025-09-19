# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    invoice_tags_id = fields.Many2many('sh.invoice.tags', string="Default Invoice Tags")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    invoice_tags_id = fields.Many2many(
        'sh.invoice.tags', string="Default Invoice Tags", related='company_id.invoice_tags_id', readonly=False)
