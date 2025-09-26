# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _


class DeliveryTime(models.Model):
    _name = "delivery.time"
    _description = 'delivery time'

    name = fields.Char('Description', required=True, translate=True)
    active = fields.Boolean('Active', default=True)
    weeks = fields.Integer('Weeks')
    months = fields.Integer('Months')