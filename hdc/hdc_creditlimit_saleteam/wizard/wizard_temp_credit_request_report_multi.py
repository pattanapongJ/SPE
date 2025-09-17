# -*- coding: utf-8 -*-

from odoo import api, fields, models
import datetime

class WizardTempCreditRequestReportMulti(models.TransientModel):
    _name = 'wizard.temp.credit.request.report.multi'
    _description = 'wizard.temp.credit.request.report.multi'

    partner_id  = fields.Many2one('res.partner',string="Customers")
    user_employee_id = fields.Many2one('hr.employee', string = 'Sale Person',)
    document_state = fields.Selection([
            ("draft", "Draft"),
            ("waiting_approval", "Waiting Approval"),
            ("approved", "Done"),
            ("cancel", "Cancelled")], "Document Status",required=True,default="waiting_approval")
    document_type = fields.Selection([
            ("single", "แบบฟอร์มขออนุมัติวงเงิน(ชั่วคราว) 1 ต่อ 1"),
            ("all", "แบบฟอร์มขออนุมัติวงเงิน(ชั่วคราว) แบบรวมที่ค้างอนุมัติ"),
            ("multi","แบบฟอร์มขออนุมัติวงเงิน(ชั่วคราว) เลือกพิมพ์เฉพาะที่เลือก")
        ],
        string="Document Type",required=True,default='multi',
        )
    temp_credit_ids = fields.Many2many('temp.credit.request', string = 'Temp Credit Request',required=True,domain=lambda self: [
            ('state', '=', self.document_state)
        ])
    
    @api.onchange('partner_id','user_employee_id','document_state')
    def _onchange_set_domain_temp_credit_ids(self):
        self.temp_credit_ids = False
        domain_temp_credit_ids = [
            ('state', '=', self.document_state),
        ]
        if self.partner_id:
            domain_temp_credit_ids.append(('partner_id', '=', self.partner_id.id))
        if self.user_employee_id:
            domain_temp_credit_ids.append(('user_employee_id', '=', self.user_employee_id.id))
        return {'domain': {'temp_credit_ids': domain_temp_credit_ids}}
    
    def _prepare_report_data(self):
        data = {
            'temp_credit_ids': self.temp_credit_ids.ids,
        }
        return data
    
    def print(self):
        if self.document_type == "single":
            return self.env.ref('hdc_creditlimit_saleteam.creditlimit_request_report_single_view').report_action(self.temp_credit_ids.ids)
        if self.document_type == "all":
            return self.env.ref('hdc_creditlimit_saleteam.creditlimit_request_report_view').report_action(self.temp_credit_ids.ids)
        if self.document_type == "multi":
            data = self._prepare_report_data()
            return self.env.ref('hdc_creditlimit_saleteam.creditlimit_request_report_multi_view').report_action(self,data=data)
        return
