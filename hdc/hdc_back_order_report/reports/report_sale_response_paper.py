
from odoo import api, models, _ ,fields
from odoo.exceptions import UserError
from odoo.tools.translate import translate

import io
import base64
import xlsxwriter

import re

class ReportBackOrderPaper(models.AbstractModel):
    _name = 'report.hdc_back_order_report.back_order_with_sale_response'
    _description = 'Report Back Order Report'

    @api.model
    def _get_report_values(self, docids, data=None):

        print('---------------> back_order_with_sale_response', data)

        print('---------------> back_order_by_type', data['back_order_by_type'])

        keep_user_id = []

        domain = [
            ('last_date_delivered', '>=', data['from_date']),
            ('last_date_delivered', '<=', data['to_date'])
        ]

        user_ids = re.findall(r'\d+', data['user_id'])
        user_ids = [int(id) for id in user_ids]

        for user_id in user_ids:
            if user_id:
                user = self.env['res.partner'].browse(user_id)
                keep_user_id.append(user.id)

        if keep_user_id:
            domain.append(('salesman_id', 'in', keep_user_id))

        print('---------------> domain', domain)
        
        lines_by_sale_respond = self.env['sale.order.line'].search(domain)

        print('---------------> lines_by_sale_respond', lines_by_sale_respond)

        if lines_by_sale_respond:
            for line in lines_by_sale_respond:
                print('------------> Line', line)
                print('------------> Code',)
                print('------------> Saleperson', line.order_id.user_id.name)
                print('------------')

                print('------------> Ship date', line.last_date_delivered)
                print('------------> Cust Name', line.order_id.partner_id.name)
                print('------------> Sales order', line.order_id.name)
                print('------------> Item Number', line.product_id.default_code)
                print('------------> Product Name', line.product_id.name)
                print('------------> Unit Price', line.price_unit)
                print('------------> Discount', line.dis_price)
                print('------------> Amount ordered', (line.price_unit * line.product_uom_qty) - line.dis_price)
                print('------------> Unit', line.product_uom.name)
                print('------------> Quantity', line.product_uom_qty)
                print('------------> Delivery', line.qty_delivered)
                print('------------> Delivery Remainder', line.product_uom_qty - line.qty_delivered)
                print('------------> ค้างส่ง/ย่อย',)
                print('------------> On order',)
                print('------------> Invoice No',)
                print('------------> Spe Invoice No',)

                print('------------> Sales Spec', line.sale_spec)
                print('------------> PO ลูกค้า โครงการ',)
                print('------------> แปลง/Type/block',)
                print('------------> Transfer ShipRemain',)

                # Stock
                print('------------> คลังอื่นๆ',)
                print('------------> เสีย(NG)',)
                print('------------> ซ่อม(RP)',)
                print('------------> ฝากขาย(CG)',)
                print('------------> ห้าง(MDT)',)
                print('------------> (MO)',)

                # PO
                print('------------> สินค้าค้างรับ',)
                print('------------> Delivery Date',)
                print('------------> Buyer Group',)

                print('------------> ค้าง Transfer',)
                print('------------> คลัง F1',)
                print('------------> คลัง F2',)
                print('------------> คลัง F6',)







        report_values = {
            'lines_by_sale_respond': lines_by_sale_respond
        }

        return report_values