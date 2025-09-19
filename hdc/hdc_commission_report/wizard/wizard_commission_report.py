from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardCommissionReport(models.TransientModel):
    _name = "wizard.commission.report"
    _description = "wizard.commission.report"

    target_type = fields.Selection([
        ('user_id', 'Salesperson'),
        ('sale_spec', 'Sale Spec'),
        ('sale_manager_id', 'Sale Manager or Sales Team'),
    ], string="Commission Target",default='sale_manager_id')
    settle_type = fields.Selection([
        ('settle_payment', 'Commission by Payments'),
        ('settle_invoice', 'Commission by Invoices'),
    ], string="Settle Commission Type",default='settle_payment',tracking = True,)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    settle_commissions_id = fields.Many2one('settle.commissions', string = 'Settle Commissions')
    commission_report_configuration_id = fields.Many2one('commission.report.configuration', string = 'Commission Report',tracking = True,domain="[('target_type','=',target_type),('settle_type','=',settle_type)]")

    @api.onchange('target_type')
    def _target_type_onchange(self):
        self.commission_report_configuration_id = False
        commission_report_configuration_id_domain = [('target_type','=',self.target_type),('settle_type','=',self.settle_type)]
        return {"domain": {"commission_report_configuration_id": commission_report_configuration_id_domain}}
    
    @api.onchange('settle_type')
    def _settle_type_onchange(self):
        self.commission_report_configuration_id = False
        commission_report_configuration_id_domain = [('target_type','=',self.target_type),('settle_type','=',self.settle_type)]
        return {"domain": {"commission_report_configuration_id": commission_report_configuration_id_domain}}
    
    def check_commission_type(self):
        return len(self.commission_report_configuration_id.commission_report_configuration_line)
    
    @api.onchange('commission_report_configuration_id')
    def _commission_report_configuration_id_onchange(self):
        report_config = self.commission_report_configuration_id
        if report_config.is_requried_commission:
            count_commission = self.check_commission_type()
            if count_commission != report_config.number_commission_type:
                raise UserError(_('Invalid commission types.\nPlease config %d commission types of "%s" at Commission Report Configuration.') % (report_config.number_commission_type,report_config.name))
        
    def print(self):
        self.ensure_one()
        report = self.commission_report_configuration_id.report_id
        report.report_file = self.commission_report_configuration_id.name +'-' + self.settle_commissions_id.name
        return report.report_action(self)
            