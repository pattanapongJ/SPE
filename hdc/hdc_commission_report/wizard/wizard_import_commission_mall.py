from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

import xlrd
import tempfile
import binascii

class WizardImportCommissionMall(models.TransientModel):
    _name = "wizard.import.commission.mall"
    _description = "wizard.import.commission.mall"

    settle_commissions_mall_id = fields.Many2one('settle.commissions.mall', string = 'Settle Commissions Mall')
    import_file = fields.Binary('Import File')
    filename = fields.Char('File Name')

    def button_import_xlsx_commission_mall(self):
        try:
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.import_file))
            fp.seek(0)
            fp.close
        except:
            raise UserError("Invalid File!")

        workbook = xlrd.open_workbook(fp.name, on_demand=True)
        sheet = workbook.sheet_by_index(0)

        if sheet.ncols == 0:
            return

        for row in range(2, sheet.nrows):
            commission_sold_out_lines_id = False
            commission_sold_out_lines = False
            for col in range(sheet.ncols):
                if col == 0:
                    commission_sold_out_lines_id = int(sheet.cell_value(row, col))
                    commission_sold_out_lines = self.env['settle.commissions.mall.sold.out.line'].search([('id', '=', commission_sold_out_lines_id)])
                elif col == 3:
                    commission_sold_out_lines.sold_out_amount_tax = sheet.cell_value(row, col)
                elif col == 4:
                    commission_sold_out_lines.sold_out_amount_untax = sheet.cell_value(row, col)
                elif col == 5:
                    expenses_rate = sheet.cell_value(row, col)
                    if isinstance(expenses_rate, float) :
                        expenses_rate = str(round(expenses_rate * 100, 2)) + '%'
                    commission_sold_out_lines.expenses_rate = expenses_rate
                elif col == 6:
                    commission_sold_out_lines.expenses_value = sheet.cell_value(row, col)
                elif col == 8:
                    commission_sold_out_lines.cal_com_value = sheet.cell_value(row, col)
                elif col == 9:
                    commission_rate = sheet.cell_value(row, col)
                    if isinstance(commission_rate, float) :
                        commission_rate = str(round(commission_rate * 100, 2)) + '%'
                    commission_sold_out_lines.commission_rate = commission_rate
                elif col == 10:
                    commission_sold_out_lines.commission_value = sheet.cell_value(row, col)
                elif col == 11:
                    commission_sold_out_lines.deduct_commission = sheet.cell_value(row, col)
        