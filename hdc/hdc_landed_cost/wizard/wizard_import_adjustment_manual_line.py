from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

import xlrd
import tempfile
import binascii

class WizardAdjustmentManualLine(models.TransientModel):
    _name = "wizard.import.adjustment.manual.line"
    _description = "wizard.import.adjustment.manual.line"

    cost_id = fields.Many2one('stock.landed.cost', string = 'Landed Cost')
    import_file = fields.Binary('Import File')
    filename = fields.Char('File Name')

    def button_import_xlsx_adjustment_manual_line(self):
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
        
        for row in range(1, sheet.nrows):
            valuation_adjustment_manual_lines_id = False
            valuation_adjustment_manual_lines = False
            for col in range(sheet.ncols):
                if col == 0:
                    valuation_adjustment_manual_lines_id = int(sheet.cell_value(row, col))
                    valuation_adjustment_manual_lines = self.env['stock.valuation.adjustment.manual.lines'].search([('id', '=', valuation_adjustment_manual_lines_id)])
                elif col == 3:
                    valuation_adjustment_manual_lines.free_product = sheet.cell_value(row, col)
                elif col == 4:
                    valuation_adjustment_manual_lines.no_cal_landed_cost = sheet.cell_value(row, col)
                elif col == 6:
                    valuation_adjustment_manual_lines.quantity = sheet.cell_value(row, col)
                elif col == 9:
                    valuation_adjustment_manual_lines.amount_price = sheet.cell_value(row, col)
                elif col == 10:
                    valuation_adjustment_manual_lines.discount = sheet.cell_value(row, col)
                elif col == 11:
                    valuation_adjustment_manual_lines.rate_usd = sheet.cell_value(row, col)
                elif col == 12:
                    valuation_adjustment_manual_lines.price_item = sheet.cell_value(row, col)
                elif col == 13:
                    valuation_adjustment_manual_lines.free_item = sheet.cell_value(row, col)
                elif col == 14:
                    valuation_adjustment_manual_lines.amount_item= sheet.cell_value(row, col)
                elif col == 15:
                    valuation_adjustment_manual_lines.duty = sheet.cell_value(row, col)
                elif col == 16:
                    valuation_adjustment_manual_lines.duty_avg = sheet.cell_value(row, col)
                elif col == 17:
                    valuation_adjustment_manual_lines.duty_avg2 = sheet.cell_value(row, col)
                elif col == 18:
                    valuation_adjustment_manual_lines.duty_avg_total = sheet.cell_value(row, col)
                elif col == 19:
                    valuation_adjustment_manual_lines.sh_avg = sheet.cell_value(row, col)
                elif col == 20:
                    valuation_adjustment_manual_lines.do_avg = sheet.cell_value(row, col)
                elif col == 21:
                    valuation_adjustment_manual_lines.ins_avg = sheet.cell_value(row, col)
                elif col == 22:
                    valuation_adjustment_manual_lines.total_duty_sh = sheet.cell_value(row, col)
                elif col == 24:
                    valuation_adjustment_manual_lines.landed_value = sheet.cell_value(row, col)
        