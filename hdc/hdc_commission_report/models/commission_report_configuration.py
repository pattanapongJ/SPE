from odoo import api, fields, models

class CommissionReportConfiguration(models.Model):
    _name = "commission.report.configuration"
    _description = "Commission Report Configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    
    code = fields.Char(string = "Report Code", required=True, tracking = True)
    name = fields.Char(string = "Report Name", required=True, tracking = True)
    description = fields.Text(string = "Description", tracking = True)
    target_type = fields.Selection([
        ('user_id', 'Salesperson'),
        ('sale_spec', 'Sale Spec'),
        ('sale_manager_id', 'Sale Manager or Sales Team'),
    ], string="Commission Target",default='sale_manager_id')
    settle_type = fields.Selection([
        ('settle_payment', 'Commission by Payments'),
        ('settle_invoice', 'Commission by Invoices'),
    ], string="Settle Commission Type",default='settle_payment',tracking = True,)
    commission_report_configuration_line = fields.One2many('commission.report.configuration.line', 'commission_report_configuration_id', string = 'Commission Types')
    report_id = fields.Many2one('ir.actions.report', string = 'Report' , domain="[('model', '=', 'wizard.commission.report')]",)
    is_requried_commission = fields.Boolean(string ="Required Commission Types", tracking = True)
    number_commission_type = fields.Integer(string="Number of Commission Types",tracking = True)
class CommissionReportConfigurationLine(models.Model):
    _name = "commission.report.configuration.line"
    _description = "Commission Report Configuration Line"

    commission_report_configuration_id = fields.Many2one('commission.report.configuration', string = 'Commission Report Configuration')
    commission_type = fields.Many2one('commission.type', string = 'Commission Types',tracking = True,)
    name = fields.Char(string = "Display Name", required=True, tracking = True)
    code = fields.Char(string = "Code", required=True, tracking = True)
    description = fields.Char(string = "Description", tracking = True)
    is_active = fields.Boolean(string ="Active", tracking = True)

    @api.onchange('commission_type')
    def _commission_type_onchange(self):
        self.name = self.commission_type.name
        self.code = self.commission_type.code
        self.description = self.commission_type.description
        self.is_active = self.commission_type.is_active