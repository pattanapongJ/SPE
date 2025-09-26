from odoo import _, models
from datetime import date, datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta

class ScrapReportXLSX(models.AbstractModel):
    _name = "report.report_scrap_xlsx"
    _description = "Scrap Report"
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, value):

        # format
        top_cell_format = workbook.add_format({"bold": True, "align": "center", "border": True})
        # top_cell_format.set_font_size(16)
        top_cell_format.set_align("vcenter")
        head_cell_format = workbook.add_format({"align": "center", "border": True})
        head_cell_format.set_font_size(12)
        head_cell_format.set_align("vcenter")
        data_cell_format = workbook.add_format({"border": True})
        data_cell_format_right = workbook.add_format({"align": "right", "border": True})

        format_footerC_bold2_2_2 = workbook.add_format({"align": "center", "bottom": True, "left": True, "right": True})
        format_footerC_bold2_2_3 = workbook.add_format({"align": "center", "left": True, "right": True})
        format_footerC_bold2_2_3.set_font_size(11)
        format_footerC_bold2_2_3.set_font_size(11)

        # # report name
        report_name = "Scarp Report"
        sheet = workbook.add_worksheet(report_name)

        for rec in range(33):
            sheet.set_column(0, rec, 20)

            # date from - date to
            day_to = ''
            text_month_to = ''
            year_to = ''
            day_from = ''
            text_month_from = ''
            year_from = ''
            date_from = value.start_date
            date_to = value.end_date

            if date_from:
                day_from = str(date_from).split('-')[2]
                month_from = str(date_from).split('-')[1]
                year_from = str(date_from).split('-')[0]
                if month_from:
                    if int(month_from) == 1:
                        text_month_from = 'มกราคม'
                    if int(month_from) == 2:
                        text_month_from = 'กุมภาพันธ์'
                    if int(month_from) == 3:
                        text_month_from = 'มีนาคม'
                    if int(month_from) == 4:
                        text_month_from = 'เมษายน'
                    if int(month_from) == 5:
                        text_month_from = 'พฤษภาคม'
                    if int(month_from) == 6:
                        text_month_from = 'มิถุนายน'
                    if int(month_from) == 7:
                        text_month_from = 'กรกฎาคม'
                    if int(month_from) == 8:
                        text_month_from = 'สิงหาคม'
                    if int(month_from) == 9:
                        text_month_from = 'กันยายน'
                    if int(month_from) == 10:
                        text_month_from = 'ตุลาคม'
                    if int(month_from) == 11:
                        text_month_from = 'พฤศจิกายน'
                    if int(month_from) == 12:
                        text_month_from = 'ธันวาคม'
                if year_from:
                    year_from = int(year_from) + 543

            if date_to == False:
                date_to = date.today()

            if date_to:
                day_to = str(date_to).split('-')[2]
                month_to = str(date_to).split('-')[1]
                year_to = str(date_to).split('-')[0]
                if month_to:
                    if int(month_to) == 1:
                        text_month_to = 'มกราคม'
                    if int(month_to) == 2:
                        text_month_to = 'กุมภาพันธ์'
                    if int(month_to) == 3:
                        text_month_to = 'มีนาคม'
                    if int(month_to) == 4:
                        text_month_to = 'เมษายน'
                    if int(month_to) == 5:
                        text_month_to = 'พฤษภาคม'
                    if int(month_to) == 6:
                        text_month_to = 'มิถุนายน'
                    if int(month_to) == 7:
                        text_month_to = 'กรกฎาคม'
                    if int(month_to) == 8:
                        text_month_to = 'สิงหาคม'
                    if int(month_to) == 9:
                        text_month_to = 'กันยายน'
                    if int(month_to) == 10:
                        text_month_to = 'ตุลาคม'
                    if int(month_to) == 11:
                        text_month_to = 'พฤศจิกายน'
                    if int(month_to) == 12:
                        text_month_to = 'ธันวาคม'
                if year_to:
                    year_to = int(year_to) + 543

        date_show = 'ระหว่างวันที่ ' + str(day_from) + ' ' + str(text_month_from) + ' ' + str(year_from) + ' ถึงวันที่ ' + str(
            day_to) + ' ' + str(text_month_to) + ' ' + str(year_to)

        sheet.merge_range(0, 0, 2, 11, 'บริษัท %s \n รายงาน Scrap ชำรุดเสียหาย \n %s' %(self.env.user.company_id.name, date_show), top_cell_format)

        sheet.write(4, 0, "ลำดับที่", head_cell_format)
        sheet.write(4, 1, "เลขที่เอกสาร", head_cell_format)
        sheet.write(4, 2, "รหัสสินค้า", head_cell_format)
        sheet.write(4, 3, "ชื่อสินค้า", head_cell_format)
        sheet.write(4, 4, "อ้างอิงเอกสาร", head_cell_format)
        sheet.write(4, 5, "วันที่บันทึก Scrap", head_cell_format)
        sheet.write(4, 6, "Lot serial number", head_cell_format)
        sheet.write(4, 7, "จำนวน", head_cell_format)
        sheet.write(4, 8, "หน่วยนับ", head_cell_format)
        sheet.write(4, 9, "สาเหตุของดารชำรุด", head_cell_format)
        sheet.write(4, 10, "หมายเหตุ",head_cell_format)
        sheet.write(4, 11, "มูลค่า", head_cell_format)

        multi_scrap_id = self.env["multi.stock.scrap"].search([
            ("scheduled_date", ">=", value.start_date.strftime("%Y-%m-%d 00:00:00")),
            ("scheduled_date", "<=", value.end_date.strftime("%Y-%m-%d 23:59:59"))])

        num = 4
        i = 0
        for scarp in multi_scrap_id:
            if value.state:
                scrap_line = scarp.scrap_line.filtered(lambda l: l.state == value.state)
            else:
                scrap_line = scarp.scrap_line

            for item in scrap_line:
                num += 1
                i += 1
                data_list = [i,
                             scarp.name or "",
                             item.product_id.default_code or "",
                             item.product_id.name or "",
                             scarp.origin or "",
                             "%s%s" %(str(scarp.scheduled_date.strftime("%d/%m/")), str(int(scarp.scheduled_date.strftime("%Y")) + 543)),
                             item.lot_id.name or "",
                             item.scrap_qty,
                             item.product_uom_id.name or "",
                             item.reason_scrap_id.name or "",
                             item.remark_note or "",
                             item.product_id.standard_price,
                             ]

                sheet.write_row(num,0, data_list, data_cell_format)

