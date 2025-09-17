# -*- coding: utf-8 -*-

import time
from odoo import api, models, _ ,fields
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta

class ReportQuotationTHDis(models.AbstractModel):
    _name = 'report.hdc_sale_agreement_reports.hdc_bk_th_dis_report'
    _description = 'Reports Quotation TH Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_blanket_id", False)
        docs = self.env['sale.blanket.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        # name_revision = ""
        # for doc in docs:
        #     if type == "revise":
        #         name_revision = doc.unrevisioned_name
        #     else:
        #         name_revision = doc.name
        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.blanket.order',
            'docs': docs,
            # 'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values

class ReportQuotationTHNoDis(models.AbstractModel):
    _name = 'report.hdc_sale_agreement_reports.hdc_bk_th_no_dis_report'
    _description = 'Reports Quotation TH No Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_blanket_id", False)
        docs = self.env['sale.blanket.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        # name_revision = ""
        # for doc in docs:
        #     if type == "revise":
        #         name_revision = doc.unrevisioned_name
        #     else:
        #         name_revision = doc.name
        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.blanket.order',
            'docs': docs,
            # 'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values

class ReportQuotationENDis(models.AbstractModel):
    _name = 'report.hdc_sale_agreement_reports.hdc_bk_en_dis_report'
    _description = 'Reports Quotation EN Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_blanket_id", False)
        docs = self.env['sale.blanket.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        # name_revision = ""
        # for doc in docs:
        #     if type == "revise":
        #         name_revision = doc.unrevisioned_name
        #     else:
        #         name_revision = doc.name
        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.blanket.order',
            'docs': docs,
            # 'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values

class ReportQuotationENNoDis(models.AbstractModel):
    _name = 'report.hdc_sale_agreement_reports.hdc_bk_en_no_dis_report'
    _description = 'Reports Quotation EN No Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_blanket_id", False)
        docs = self.env['sale.blanket.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        # name_revision = ""
        # for doc in docs:
        #     if type == "revise":
        #         name_revision = doc.unrevisioned_name
        #     else:
        #         name_revision = doc.name
        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.blanket.order',
            'docs': docs,
            # 'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values
    

class ReportBKProDis(models.AbstractModel):
    _name = 'report.hdc_sale_agreement_reports.hdc_bk_pro_en_dis_report'
    _description = 'Reports BK EN Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_blanket_id", False)
        docs = self.env['sale.blanket.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.blanket.order',
            'docs': docs,
            'description_type': description_type,
        }
        return report_values

class ReportBKProNoDis(models.AbstractModel):
    _name = 'report.hdc_sale_agreement_reports.hdc_bk_pro_en_no_dis_report'
    _description = 'Reports BK EN No Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_blanket_id", False)
        docs = self.env['sale.blanket.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.blanket.order',
            'docs': docs,
            'description_type': description_type,
        }
        return report_values
    
#########################################