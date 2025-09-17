from datetime import date

from odoo import api, fields, models, _
from datetime import datetime

class HrEmployeePrivate(models.Model):
    _inherit = "hr.employee"

    employee_id2 = fields.Char('Employee ID2')

    sale_team_id = fields.Many2one('crm.team', 'Sale Team')
    sale_spec_team_id = fields.Many2one('crm.team', 'Sale Team')
    is_sale_spec = fields.Boolean(string='Is Sale Spec')
    sale_spec_detail = fields.Text("Sale Spec Detail")