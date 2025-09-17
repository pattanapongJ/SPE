# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from random import randint

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

class Repair(models.Model):
    _inherit = 'repair.order'

    def _default_employee(self):
        employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id), ("company_id", "=", self.env.user.company_id.id)], limit=1)
        if not employee_id:
            employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)], limit=1)
        return employee_id.id
    
    user_id = fields.Many2one('res.users', string="Responsible user", default=lambda self: self.env.user, check_company=False)
    user_employee_id = fields.Many2one('hr.employee', string="Responsible", default=lambda self: self._default_employee(),)
    
    @api.onchange("user_employee_id")
    def _onchange_user_employee_id(self):
        if self.user_employee_id.user_id:
            self.user_id = self.user_employee_id.user_id