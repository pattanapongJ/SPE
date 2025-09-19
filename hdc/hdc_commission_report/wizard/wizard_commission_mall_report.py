from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardCommissionMallReport(models.TransientModel):
    _name = "wizard.commission.mall.report"
    _description = "wizard.commission.mall.report"

    target_type = fields.Selection([
        ('normal', 'Normal'),
        ('sold_out', 'Sold Out'),
    ], string="Commission Type",default='normal')

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    settle_commissions_mall_id = fields.Many2one('settle.commissions.mall', string = 'Settle Commissions Mall')
    commission_mall_report_configuration_id = fields.Many2one('commission.mall.report.configuration', string = 'Commission Mall Report',tracking = True,domain="[('target_type','=',target_type)]")

    @api.onchange('target_type')
    def _target_type_onchange(self):
        commission_mall_report_configuration_id_domain = [('target_type','=',self.target_type)]
        return {"domain": {"commission_mall_report_configuration_id": commission_mall_report_configuration_id_domain}}
        
    def print(self):
        self.ensure_one()
        report = self.commission_mall_report_configuration_id.report_id
        report.report_file = self.commission_mall_report_configuration_id.name +'-' + self.settle_commissions_mall_id.name
        return report.report_action(self)
            