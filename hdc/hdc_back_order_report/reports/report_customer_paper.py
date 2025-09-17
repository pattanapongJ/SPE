
from odoo import api, models, _ ,fields
from odoo.exceptions import UserError
from odoo.tools.translate import translate

import io
import base64
import xlsxwriter

import re

class ReportBackOrderPaper(models.AbstractModel):
    _name = 'report.hdc_back_order_report.back_order_with_customer'
    _description = 'Report Back Order Report'

    @api.model
    def _get_report_values(self, docids, data=None):

        print('---------------> data', data)

        print('---------------> back_order_by_type', data['back_order_by_type'])

        keep_customer_id = []

        domain = [
            ('last_date_delivered', '>=', data['from_date']),
            ('last_date_delivered', '<=', data['to_date'])
        ]

        customer_ids = re.findall(r'\d+', data['partner_id'])
        customer_ids = [int(id) for id in customer_ids]

        for customer_id in customer_ids:
            if customer_id:
                partner = self.env['res.partner'].browse(customer_id)
                keep_customer_id.append(partner.id)

        if keep_customer_id:
            domain.append(('order_partner_id', 'in', keep_customer_id))

        # print('---------------> domain', domain)
        
        lines_by_customer = self.env['sale.order.line'].search(domain)

        # print('---------------> lines_by_customer', lines_by_customer)

        if lines_by_customer:
            for line in lines_by_customer:
                print('------------> Line', line)
                print('------------> Ref', line.order_partner_id.ref)
                print('------------> Customer', line.order_partner_id.name)
                print('------------')

                print('------------> Ship date', line.last_date_delivered)
                print('------------> Sales order', line.order_id.name)
                print('------------> Item Number', line.product_id.default_code)
                print('------------> Item Name', line.product_id.name)
                print('------------> SO Status', 'Backorder')
                print('------------> Line Status', 'Backorder')
                print('------------> Remark', line.note)
                print('------------> Unit Price', line.price_unit)
                print('------------> Discount', line.dis_price)
                print('------------> Amount ordered', (line.price_unit * line.product_uom_qty) - line.dis_price)
                print('------------> Unit', line.product_uom.name)
                print('------------> Quantity', line.product_uom_qty)
                print('------------> Delivery', line.qty_delivered)
                print('------------> Delivery Remainder', line.product_uom_qty - line.qty_delivered)
                print('------------> ค้างส่ง/ย่อย',)

                print('------------> Invoice No.', )
                print('------------> Spe Invoice No.',)
                print('------------> Sales Spec', line.sale_spec)
                print('------------> Sales Responsible', line.user_id.name)
                print('------------> Sales Taker', line.user_sale_agreement.name)
                print('------------> pool',)
                print('------------> PO ลูกค้า โครงการ',)
                print('------------> Picking Note',)
                print('------------> Transfer ShipRemain',)
                print('------------> Po สินค้าค้างรับ',)
                print('------------> Delivery Date',)
                print('------------> Onhand',)
                print('------------> ค้าง Transfer',)
                print('------------> แปลง/Type/block',)


        report_values = {
            'lines_by_customer': lines_by_customer
        }

        return report_values