# -*- coding: utf-8 -*-

import time
from odoo import api, models, _ ,fields
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta


class ReportTaxIVPreprint(models.AbstractModel):
    _name = 'report.hdc_account_general_reports.mpf_tax_inv_pp_report'
    _description = 'Report Tax invoice Project'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids)

        form_label_types = set(docs.mapped('form_label_type'))
        error_message = ""
        if len(form_label_types) > 1:
            error_message = "กรุณาเลือกแบบ Form Label ในหน้าใบ Invoice ให้ตรงกัน ก่อนทำการ Preview รายงาน"

        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': docs,
            'error_message': error_message,
            'show_digits': self.show_digits,
        }
        
    def show_digits(self, number):
        number_str = str(number)
        parts = number_str.split('.')

        if len(parts) == 1:
            return

        integer_part = parts[0]
        decimal_part = parts[1]

        if len(decimal_part) < 2:
            return f"{integer_part}.{decimal_part.ljust(2, '0')}"
        elif len(decimal_part) == 3:
            return f"{integer_part}.{decimal_part}"
        elif 3 < len(decimal_part) < 4:
            return f"{integer_part}.{decimal_part}"
        else:
            return number_str
class ReportPreprintIV(models.AbstractModel):
    _name = 'report.hdc_account_general_reports.preprint_project_report'
    _description = 'Report PrePrint Project'

        
    @api.model
    def _get_report_values(self, docids, data=None):

        # print('--------->docids', docids)
        
        docs = self.env['account.move'].browse(docids)

        # print('--------->docs', docs)
        
        # sale_order = self.env['sale.order'].search([('name', '=', docs.invoice_origin)])

        report_values = {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'docs': docs,
            # 'sale_order': sale_order,
        }
        return report_values

class ReportPreprintIvPjDep(ReportPreprintIV):
    _name = 'report.hdc_account_general_reports.ac_tax_inv_pj_dep_report'
    _description = 'account_tax_inv pj deposit report'

class ReportPreprintIvPjRe(ReportPreprintIV):
    _name = 'report.hdc_account_general_reports.ac_tax_inv_pj_de_re_report'
    _description = 'account tax inv pj deposit re report'