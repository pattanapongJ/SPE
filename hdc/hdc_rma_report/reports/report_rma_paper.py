from odoo import api, models, _ ,fields
from odoo.exceptions import UserError
from odoo.tools.translate import translate

import io
import base64
import xlsxwriter

class ReportRmaPaper(models.AbstractModel):
    _name = 'report.hdc_rma_report.hdc_rma_report'
    _description = 'Report RMA All'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['crm.claim.ept'].browse(docids)

        is_dewalt = data['is_dewalt']
        out_of_warranty = data['out_of_warranty']
        under_warranty = data['under_warranty']
        start_date = data['start_date']
        end_date = data['end_date']
        list_job_on = data['keep_job_no_ids']
        list_product_id_selected = data['keep_product_ids']

        if len(list_job_on) > 0:
            domain = [
                ('date', '>=', start_date),
                ('date', '<=', end_date),
                ('is_job_no', 'in', list_job_on)
            ]
        else:
            domain = [
                ('date', '>=', start_date),
                ('date', '<=', end_date)
            ]

        if is_dewalt:
            domain.append(('is_dewalt', '=', True))
            if out_of_warranty and under_warranty:
                domain.append(('warranty_type', 'in', ['out', 'under']))
            elif out_of_warranty:
                domain.append(('warranty_type', '=', 'out'))
            elif under_warranty:
                domain.append(('warranty_type', '=', 'under'))

        record_RMA_filter = self.env['crm.claim.ept'].search(domain)   

        report_values = {
            'record_RMA_filter': record_RMA_filter,
            'list_product_id_selected': list_product_id_selected
        }

        return report_values