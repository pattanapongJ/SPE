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
class WizardSaleInterCompanyReport(models.TransientModel):
    _name = "wizard.sale.inter.company.report"

    from_date = fields.Date(string="From Invoice Date", required=True)
    to_date = fields.Date(string="To", required=True)
    product_ids = fields.Many2many(comodel_name="product.product",string="Product")
    tax = fields.Selection(
        selection=[("non_vat", "Non Vat"), 
                   ("included", "Included"), 
                   ("vat_ex", "Vat Excluded"), 
                   ("all", "All")],
        string="Tax",
        # default="so_po",
    )

    def print_excel(self):

        report = self.env['ir.actions.report'].search(
                [('report_name', '=', 'sale_inter_company_xlsx'),
                ('report_type', '=', 'xlsx')], limit=1)
        return report.report_action(self)