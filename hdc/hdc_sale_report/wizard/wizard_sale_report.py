# -*- coding: utf-8 -*-

from odoo import api, fields, models
import datetime

class WizardSaleReporting(models.TransientModel):
    _name = 'wizard.sale.reporting'
    _description = 'Wizard Sale Reporting'

    document_type = fields.Selection([
            ("category", "Product Category"),
            ("brand", "Product Brand"), 
            ("customer", "Customer"),
            ("sale", "Sale person"),
        ],
        string="Sale Report Types", required=True,default='category')
    
    start_date  = fields.Date(string = "Start Date", required=True)
    end_date    = fields.Date(string = "End Date", required=True)
    saleman_id  = fields.Many2many('res.users', string="Sale Persons")
    saleteam_id = fields.Many2many('crm.team',string="Sale Teams")
    categories  = fields.Many2many('product.category',string="Product Categories")
    brand_id    = fields.Many2many(comodel_name='product.brand',string="Product Brands")
    partner_id  = fields.Many2many('res.partner',string="Customers")



    def print(self):
        data ={
            'document_type':self.document_type,
            'start_date':self.start_date,
            'end_date':self.end_date,
            'saleman_id':self.saleman_id.ids,
            'saleteam_id':self.saleteam_id.ids,
            'categories':self.categories.ids,
            'brand_id':self.brand_id.ids,
            'partner_id':self.partner_id.ids,
        }
        current_date = datetime.datetime.now()
        formatted_date = current_date.strftime('%d%m%Y')

        report_obj = self.env.ref('hdc_sale_report.sale_report_categorie_detail_excel_view')
        if self.document_type == "sale":
            report_obj.report_file = "รายงานยอดขายพนักงาน_{}".format(formatted_date)
        elif self.document_type == "category":
            report_obj.report_file = "รายงานยอดขายประเภทสินค้า_{}".format(formatted_date)
        elif self.document_type == "customer":
            report_obj.report_file = "รายงานจัดลำดับยอดขายตามลูกค้า_{}".format(formatted_date)
        elif self.document_type == "brand":
            report_obj.report_file = "รายงานยอดขายตามยี่ห้อ_{}".format(formatted_date)

        return report_obj.report_action(self,data=data)
