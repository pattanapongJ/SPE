from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardSaleDewaltReport(models.TransientModel):
    _name = "wizard.sale.dewalt.report"
    _description = "wizard sale dewalt report"

    document = fields.Selection([
        ("delivery", "ใบส่งของ"),
        ("claim", "ใบส่งงานเคลม"),
    ],
    string="Documents", required=True, default='delivery'
    )

    sale_id = fields.Many2one('sale.order', string='SO')
    
    def print(self):
                
        if self.document == "delivery":
            return self.env.ref('hdc_rma_dewalt.delivery_dewalt_report_view').report_action(self.sale_id)
        else:
            return self.env.ref('hdc_rma_dewalt.claim_dewalt_report_view').report_action(self.sale_id)
        