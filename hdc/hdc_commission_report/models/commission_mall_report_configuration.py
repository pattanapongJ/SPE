from odoo import api, fields, models

class CommissionMallReportConfiguration(models.Model):
    _name = "commission.mall.report.configuration"
    _description = "Commission Mall Report Configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    
    code = fields.Char(string = "Report Code", required=True, tracking = True)
    name = fields.Char(string = "Report Name", required=True, tracking = True)
    description = fields.Text(string = "Description", tracking = True)
    target_type = fields.Selection([
        ('normal', 'Normal'),
        ('sold_out', 'Sold Out'),
    ], string="Commission Type",default='normal')
    report_id = fields.Many2one('ir.actions.report', string = 'Report' , domain="[('model', '=', 'wizard.commission.mall.report')]",)