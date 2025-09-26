# -*- coding: utf-8 -*-

import time
from odoo import api, models, _ ,fields
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta

class ReportProformaENDis(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_proforma_en_dis_report'
    _description = 'Reports PROFORMA EN Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values
    
class ReportProformaENNODis(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_proforma_en_no_dis_report'
    _description = 'Reports PROFORMA EN NO Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values

class ReportQuotationTHDis(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_quotation_th_dis_report'
    _description = 'Reports Quotation TH Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values
    
class ReportQuotationDTHDis(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_q_d_th_dis_report'
    _description = 'Reports Quotation Debt TH Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values

class ReportQuotationTHNoDis(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_quotation_th_no_dis_report'
    _description = 'Reports Quotation TH No Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values
    
class ReportQuotationDTHNoDis(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_q_d_th_no_dis_report'
    _description = 'Reports Quotation Debt TH No Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values

class ReportQuotationENDis(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_quotation_en_dis_report'
    _description = 'Reports Quotation EN Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values

class ReportQuotationENNoDis(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_quotation_en_no_dis_report'
    _description = 'Reports Quotation EN No Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values
    
#########################################

class ReportSaleTHDis(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_sale_order_th_dis_report'
    _description = 'Report Sale Order TH Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values
    
class ReportSaleDTHDis(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_sale_d_th_dis_report'
    _description = 'Report Sale Order Debt TH Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values

class ReportSaleTHNoDis(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_sale_order_th_no_dis_report'
    _description = 'Report Sale Order TH No Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values
    
class ReportSaleDTHNoDis(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_sale_d_th_no_dis_report'
    _description = 'Report Sale Order Debt TH No Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values

class ReportSaleENDis(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_sale_order_en_dis_report'
    _description = 'Report Sale Order EN Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values

class ReportSaleENNoDis(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_sale_order_en_no_dis_report'
    _description = 'Report Sale Order EN No Dis'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        description_type = data.get("description_type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
            'description_type': description_type,
        }
        return report_values
    

################################
class ReportDeliveryBoothsQO(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_delivery_booth_qo_report'
    _description = 'Report Delivery Booth QO'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
        }
        return report_values

class ReportDeliveryBoothsSO(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_delivery_booth_so_report'
    _description = 'Report Delivery Booth SO'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
        }
        return report_values
    
class ReportDeliveryBoothsEN(models.AbstractModel):
    _name = 'report.hdc_sale_general_reports.hdc_delivery_booth_en_report'
    _description = 'Report Delivery Booth EN'

        
    @api.model
    def _get_report_values(self, docids, data=None):
        ids = data.get("sale_id", False)
        docs = self.env['sale.order'].browse(ids)
        type = data.get("type", False)
        name_revision = ""
        for doc in docs:
            if type == "revise":
                name_revision = doc.unrevisioned_name
            else:
                name_revision = doc.name

        report_values = {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
            'name_revision': name_revision,
        }
        return report_values