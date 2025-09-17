# -*- coding: utf-8 -*-

import json

from odoo import api, models, _
from odoo.tools import float_round


class ReportTaxReport(models.AbstractModel):
    _name = 'report.l10n_th_tax_report.report_tax_report_pdf'
    _description = 'Tax Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['report.tax.report'].browse(docids)
        report_pages = {}
        for doc in docs:
            report_pages[doc.id] = self.calculate_subtotals(doc)
        return {
            'doc_ids': docids,
            'doc_model': self.env['report.tax.report'],
            'data': data,
            'docs': docs,
            'report_pages': report_pages
        }

    def calculate_subtotals(self, doc):
        lines_per_page = 25  # Approximation of lines per page
        pages = []  # List to hold pages with their lines and subtotal
        current_page = []
        line_counter = 0

        doc_results = doc.get_line_data()

        for line in doc_results:
            current_page.append(line)
            line_counter += len(line['voucher_no']) or 1

            if line_counter >= lines_per_page:
                pages.append({
                    'lines': current_page
                })
                current_page = []
                line_counter = 0

        # Add remaining lines to the last page
        if current_page:
            pages.append({
                'lines': current_page
            })

        return pages

