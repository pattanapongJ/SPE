
from odoo import api, fields, models

class IrActionsReportInherit(models.Model):
    _inherit = 'ir.actions.report'
    
    iso_name = fields.Char(string="ISO")
