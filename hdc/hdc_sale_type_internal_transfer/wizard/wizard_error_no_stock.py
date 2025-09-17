# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError

class WizardErrorNoStock(models.TransientModel):
    _name = 'wizard.error.no.stock'
    _description = "Wizard Error No Stock"

    order_id = fields.Many2one(comodel_name = "sale.order", string = "Sale order")