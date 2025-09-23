from odoo import api, fields, models

class InternalAccountStatementReportWizard(models.TransientModel):
    _name = 'internal.acc.stmt.report.wizard'
    _description = 'A interface for creating internal account statment report'
    
    company_id      = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    partner_id      = fields.Many2one('res.partner', string='Customer', required=True)
    sale_team_id    = fields.Many2one('crm.team', string='Sales Team')
    inv_start_date  = fields.Date(string='Invoice Start Date', default=fields.Date.context_today)
    inv_end_date  = fields.Date(string='Invoice End Date', default=fields.Date.context_today)
    
    def _print_report(self, report_type):
        self.ensure_one()
        data = self._prepare_internal_acc_stmt_report()
        report_name = "bs_internal_account_statement_report.report_acc"
        report_action = self.env["ir.actions.report"].search(
                [("report_name", "=", report_name), ("report_type", "=", report_type)],
                limit=1,
            )
        return report_action.report_action(self, data=data)
    
    def button_export_html(self):
        self.ensure_one()
        report_type = "qweb-html"
        return self._export(report_type)
    
    def button_export_pdf(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        return self._export(report_type)
    
    def _prepare_internal_acc_stmt_report(self):
        self.ensure_one()
        return {
            'wizard_id': self.id,
            'company_id': self.company_id.id,
            'date_start': self.inv_start_date,
            'date_end': self.inv_end_date,
            'partner_id': self.partner_id.id,
            'sale_team_id': self.sale_team_id.id
        }
        
    def _export(self, report_type):
        return self._print_report(report_type)