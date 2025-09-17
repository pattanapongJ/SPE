# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

import io
import base64
import xlsxwriter

from odoo.tools import format_date
from datetime import datetime, timedelta
import calendar

# Define your wizard model
class WizardSaleOrderLineReport(models.TransientModel):
    _name = "wizard.sale.order.line.report"
    _description = 'wizard sale order line report'

    from_date = fields.Date(string="From", required=True)
    to_date = fields.Date(string="To", required=True)

    order_by_type = fields.Selection([
        ('by_customer', 'ชื่อลูกค้า'),
        ('by_sale_person', 'Sale Response'),
        ('by_item', 'Item'),
    ], string="By Type", default="by_customer")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    partner_id = fields.Many2many(comodel_name="res.partner", string="Customer", domain="[('customer', '=', True)]")
    user_id = fields.Many2many(comodel_name="res.users", string="Salesperson")
    product_id = fields.Many2many('product.product',domain=[('type', '=','product')], string='Product')
    # project_name = fields.Many2one('sale.project', string='Project Name')

    def print_pdf(self):

        if self.from_date > self.to_date:
            raise UserError("Start Date Must Less Than End Date")
        

        data = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'back_order_by_type': self.back_order_by_type,
            'partner_id': self.partner_id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'project_name': self.project_name,
        }

        return self.env.ref('hdc_sale_order_line_report.back_order_report_view').report_action(self, data=data)
    
    def get_report(self):
        if self.from_date > self.to_date:
            raise UserError("Start Date Must Less Than End Date")
        if self.order_by_type == 'by_customer':
            report_name = 'so_line_customer_xlsx'
        elif self.order_by_type == 'by_sale_person':
            report_name = 'so_line_sale_xlsx'
        else:
            report_name = 'so_line_item_xlsx'
        report = self.env['ir.actions.report'].search(
            [('report_name', '=', report_name),
             ('report_type', '=', 'xlsx')], limit=1)
        return report.report_action(self)