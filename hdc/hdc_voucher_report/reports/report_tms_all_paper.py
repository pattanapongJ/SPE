
# from odoo import api, models, _ ,fields
# from odoo.exceptions import UserError
# from odoo.tools.translate import translate

# import io
# import base64
# import xlsxwriter

# class ReportTmsAllPaper(models.AbstractModel):
#     _name = 'report.hdc_tms_general_report.hdc_tms_all_report'
#     _description = 'Report TMS All'

#     @api.model
#     def _get_report_values(self, docids, data=None):
        
#         docs = self.env['stock.picking'].browse(docids)

#         domain = [
#             ('delivery_date', '>=', data['from_date']),
#             ('delivery_date', '<=', data['to_date']),
#             ('transport_desc', 'in', data['keep_transport_line_code'])
#         ]


#         distribution_deli_notes = self.env["distribition.delivery.note"].search(domain)
        

#         distribution_deli_note_search = self.env["distribition.delivery.note"].search([])

#         sum_total_price = 0
#         sum_count = 0

#         from_date = fields.Date.from_string(data['from_date'])
#         to_date = fields.Date.from_string(data['to_date'])


#         for record in distribution_deli_note_search:

#             total_price = 0

#             if record.delivery_date:
#                 if (
#                     record.delivery_date >= from_date
#                     and record.delivery_date <= to_date
#                 ):
#                     if record.transport_desc in data['keep_transport_line_code']:

#                         for line in record.invoice_line_ids:
#                             total_price += line.amount_total
                        
#                         sum_count += len(record.invoice_line_ids)
#             sum_total_price += total_price

#         str_from_date = from_date.strftime('%d-%m-%Y')
#         str_to_date = to_date.strftime('%d-%m-%Y')


#         report_values = {
#             'from_date': str_from_date,
#             'to_date': str_to_date,
#             'test_test': data['keep_transport_line_code'],
#             'distribution_deli_notes': distribution_deli_notes,
#             'sum_total_price': sum_total_price,
#             'sum_count': sum_count

#         }
#         return report_values