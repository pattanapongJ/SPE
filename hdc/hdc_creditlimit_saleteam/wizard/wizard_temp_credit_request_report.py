from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardTempCreditRequestReport(models.TransientModel):
    _name = "wizard.temp.credit.request.report"
    _description = "wizard.temp.credit.request.report"

    document = fields.Selection([
            ("single", "แบบฟอร์มขออนุมัติวงเงิน(ชั่วคราว) 1 ต่อ 1"),
            ("all", "แบบฟอร์มขออนุมัติวงเงิน(ชั่วคราว) แบบรวมที่ค้างอนุมัติ"),
        ],
        string="Document",
        )
    
    temp_credit_id = fields.Many2one('temp.credit.request', string = 'Temp Credit Request')

    def print(self):
        if self.document == "single":
            return self.env.ref('hdc_creditlimit_saleteam.creditlimit_request_report_single_view').report_action(self.temp_credit_id)
        if self.document == "all":
            return self.env.ref('hdc_creditlimit_saleteam.creditlimit_request_report_view').report_action(self.temp_credit_id)