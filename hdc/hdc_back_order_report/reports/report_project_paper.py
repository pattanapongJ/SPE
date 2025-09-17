
from odoo import api, models, _ ,fields
from odoo.exceptions import UserError
from odoo.tools.translate import translate

import io
import base64
import xlsxwriter

import re

class ReportBackOrderPaper(models.AbstractModel):
    _name = 'report.hdc_back_order_report.back_order_with_project'
    _description = 'Report Back Order Report'

    @api.model
    def _get_report_values(self, docids, data=None):

        print('---------------> back_order_with_project', data)

        print('---------------> back_order_by_type', data['back_order_by_type'])

        keep_project_id = []

        domain = [
            ('last_date_delivered', '>=', data['from_date']),
            ('last_date_delivered', '<=', data['to_date'])
        ]

        project_ids = re.findall(r'\d+', data['project_name'])
        project_ids = [int(id) for id in project_ids]

        for project_id in project_ids:
            if project_id:
                # print('--------------> project_id', project_id)
                project = self.env['sale.project'].browse(project_id)
                keep_project_id.append(project.id)

        if keep_project_id:
            domain.append(('order_id.project_name.id', 'in', keep_project_id))

        print('---------------> domain', domain)
        
        lines_by_project = self.env['sale.order.line'].search(domain)

        print('---------------> lines_by_project', lines_by_project)

        if lines_by_project:
            for line in lines_by_project:
                print('------------> Line', line)
                print('------------> Ref', line.order_partner_id.ref)
                print('------------> Customer', line.order_partner_id.name)

                # Row 1
                print('------------> Project', line.order_id.project_name.project_name)
                print('------------> Sales order', line.order_id.name)
                print('------------> PO ลูกค้า',)
                print('------------> Ship date',)
                print('------------> Sales Responsible',)
                print('------------> Sales Spec',)
                print('------------> Sales Taker',)
                print('------------> โครงการ',)
                print('------------> แปลง/type/Block',)

                # Row 2
                print('------------> Item number', line.product_id.default_code)
                print('------------> Item Name', line.product_id.name)
                print('------------> Quantity', line.product_uom_qty)
                print('------------> Delivery', line.qty_delivered)
                print('------------> Deliver Remain', line.product_uom_qty - line.qty_delivered)
                print('------------> Po ค้างรับ',)
                print('------------> Amount',)
                print('------------> WH Date',)
                print('------------> On order',)
                print('------------> Onhand',)
                print('------------> Transfer ShipRemain',)

        report_values = {
            'test': 'Test'
        }

        return report_values