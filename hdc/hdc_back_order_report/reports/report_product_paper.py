
from odoo import api, models, _ ,fields
from odoo.exceptions import UserError
from odoo.tools.translate import translate

import io
import base64
import xlsxwriter

import re

class ReportBackOrderPaper(models.AbstractModel):
    _name = 'report.hdc_back_order_report.back_order_with_product'
    _description = 'Report Back Order Report'

    @api.model
    def _get_report_values(self, docids, data=None):

        print('---------------> back_order_with_product', data)

        print('---------------> back_order_by_type', data['back_order_by_type'])

        keep_product_id = []

        domain = [
            ('last_date_delivered', '>=', data['from_date']),
            ('last_date_delivered', '<=', data['to_date'])
        ]

        product_ids = re.findall(r'\d+', data['product_id'])
        product_ids = [int(id) for id in product_ids]

        for product_id in product_ids:
            if product_id:
                product = self.env['product.product'].browse(product_id)
                keep_product_id.append(product.id)

        if keep_product_id:
            domain.append(('product_id', 'in', keep_product_id))

        print('---------------> domain', domain)
        
        lines_by_product = self.env['sale.order.line'].search(domain)

        print('---------------> lines_by_product', lines_by_product)

        if lines_by_product:
            for line in lines_by_product:
                print('------------> Line', line)
                print('------------> Item Number', line.product_id.default_code)
                print('------------> Item Name', line.product_id.name)
                print('------------')

                print('------------> Ship date', line.last_date_delivered)
                print('------------> Customer',)
                print('------------> Cust Name', line.order_partner_id.name)
                print('------------> Custname Eng',)
                print('------------> Sales order', line.order_id.name)
                print('------------> Po Date', line.order_id.po_date)
                print('------------> Req. Receipt Date', line.order_id.requested_receipt_date)
                print('------------> Req. Ship Date', )
                print('------------> Customer Req.', )
                print('------------> Delivery Date', line.order_id.commitment_date)
                print('------------> So Status', 'Backorder')



        report_values = {
            'lines_by_product': lines_by_product
        }

        return report_values