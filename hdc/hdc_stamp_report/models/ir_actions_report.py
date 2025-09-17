
from odoo import api, fields, models

class IrActionsReportInherit(models.Model):
    _inherit = 'ir.actions.report'
    
    stamp_report = fields.Char(string="Stamp")
