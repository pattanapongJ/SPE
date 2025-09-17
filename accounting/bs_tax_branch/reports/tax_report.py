from odoo import fields, models

class TaxReportView(models.TransientModel):
    _inherit = "tax.report.view"
    
    branch_id = fields.Many2one('res.branch', string='Branch')

class TaxReport(models.TransientModel):
    _inherit = "report.tax.report"
    
    branch_id = fields.Many2one('res.branch', string='Branch')
    
    def _compute_results(self):
        self.ensure_one()
        self._cr.execute(
            """
            select company_id, account_id, partner_id,
                tax_invoice_number, tax_date, name,
                sum(tax_base_amount) tax_base_amount, sum(tax_amount) tax_amount
            from (
            select t.id, t.company_id, ml.account_id, t.partner_id, t.branch_id,
              case when ml.parent_state = 'posted' and t.reversing_id is null
                then t.tax_invoice_number else
                t.tax_invoice_number || ' (VOID)' end as tax_invoice_number,
              t.tax_invoice_date as tax_date,
              case when ml.parent_state = 'posted' and t.reversing_id is null
                then t.tax_base_amount else 0.0 end as tax_base_amount,
              case when ml.parent_state = 'posted' and t.reversing_id is null
                then t.balance else 0.0 end as tax_amount,
              case when m.ref is not null
                then m.ref else ml.move_name end as name
            from account_move_tax_invoice t
              join account_move_line ml on ml.id = t.move_line_id
              join account_move m on m.id = ml.move_id
            where ml.parent_state in ('posted', 'cancel')
              and t.tax_invoice_number is not null
              and ml.account_id in (select distinct account_id
                                    from account_tax_repartition_line
                                    where account_id is not null
                                    and invoice_tax_id = %s or refund_tax_id = %s)
              and t.report_date >= %s and t.report_date <= %s
              and ml.company_id = %s
              and (%s is null and t.branch_id is null OR t.branch_id = %s)
              and t.reversed_id is null
            ) a
            group by company_id, account_id, partner_id,
                tax_invoice_number, tax_date, name
            order by tax_date, tax_invoice_number
        """,
            (
                self.tax_id.id,
                self.tax_id.id,
                self.date_from,
                self.date_to,
                self.company_id.id,
                self.branch_id.id if self.branch_id else None,
                self.branch_id.id if self.branch_id else None,
            ),
        )
        tax_report_results = self._cr.dictfetchall()
        ReportLine = self.env["tax.report.view"]
        self.results = False
        for line in tax_report_results:
            self.results += ReportLine.new(line)