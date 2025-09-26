from odoo import fields, models


class TaxReportView(models.TransientModel):
    _inherit = 'tax.report.view'

    voucher_no = fields.Char()


class TaxReport(models.TransientModel):
    _inherit = "report.tax.report"

    def _compute_results(self):
        self.ensure_one()
        # Determine if branch_id is set
        branch_id = self.branch_id.id if self.branch_id else None
        # Modify SQL query accordingly
        branch_condition = "t.branch_id is null" if not branch_id else f"t.branch_id={branch_id} "

        self._cr.execute(
            f"""
            select company_id, account_id, partner_id,
                tax_invoice_number, tax_date, name,voucher_no,
                sum(tax_base_amount) tax_base_amount, sum(tax_amount) tax_amount
            from (
            select t.id, t.company_id, ml.account_id, t.partner_id, t.branch_id,
              case when ml.parent_state = 'posted' and t.reversing_id is null
                then t.tax_invoice_number else
                t.tax_invoice_number || ' (VOID)' end as tax_invoice_number,
              m.name as voucher_no,
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
              and {branch_condition}
              and t.reversed_id is null
            ) a
            group by company_id, account_id, partner_id,
                tax_invoice_number,voucher_no, tax_date, name
            order by tax_date, tax_invoice_number
        """,
            (
                self.tax_id.id,
                self.tax_id.id,
                self.date_from,
                self.date_to,
                self.company_id.id
            ),
        )
        tax_report_results = self._cr.dictfetchall()
        ReportLine = self.env["tax.report.view"]
        self.results = False
        for line in tax_report_results:
            self.results += ReportLine.new(line)



    def get_line_data(self):
        """
        Custom method to group results by partner_id and tax_date,
        and generate a custom dictionary list, concatenating invoice_no and ref_no.
        """
        grouped_data = {}
        for line in self.results:
            # Group by partner_id and tax_date
            key = (line.partner_id.id, line.tax_date,line.tax_invoice_number)
            if key not in grouped_data:
                grouped_data[key] = {
                    'partner': line.partner_id,
                    'tax_date': line.tax_date,
                    'tax_base_amount': 0.0,
                    'tax_amount': 0.0,
                    'tax_invoice_number': line.tax_invoice_number,
                    'voucher_no': [],
                }
            # Accumulate the tax_base_amount and tax_amount for each group
            grouped_data[key]['tax_base_amount'] += line.tax_base_amount
            grouped_data[key]['tax_amount'] += line.tax_amount
            # Collect voucher_no, ensuring they are not duplicated
            grouped_data[key]['voucher_no'].append(line.voucher_no)

        # Convert the grouped data into a list of dictionaries
        grouped_results = []
        for data in grouped_data.values():
            # Join the voucher_no lists as comma-separated strings
            # data['voucher_no'] = ",".join(data['voucher_no'])
            grouped_results.append(data)

        return grouped_results

