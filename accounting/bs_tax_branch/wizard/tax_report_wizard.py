from odoo import api, fields, models

class TaxReportWizard(models.TransientModel):
    _inherit = "tax.report.wizard"
            
    branch_id = fields.Many2one('res.branch', string='Branch')
    
    def _prepare_tax_report(self):
        self.ensure_one()
        return {
            "branch_id": self.branch_id.id,
            "company_id": self.company_id.id,
            "tax_id": self.tax_id.id,
            "date_range_id": self.date_range_id.id,
            "date_from": self.date_range_id.date_start,
            "date_to": self.date_range_id.date_end,
        }
    
    