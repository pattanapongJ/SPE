# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class DriverModel(models.Model):
    _name = "driver.model"
    _description = "Driver"

    employee_id = fields.Many2one("hr.employee", string="Driver")
    name = fields.Char('Driver',related='employee_id.name')
    car_registration = fields.Char('ทะเบียนรถ')
