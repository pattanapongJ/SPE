
from odoo import api, models, _ ,fields
from datetime import datetime

to_9 = ('ศูนย์', 'หนึ่ง', 'สอง', 'สาม', 'สี่', 'ห้า', 'หก', 'เจ็ด', 'แปด', 'เก้า' )
tens = ('สิบ', 'ยี่สิบ', 'สามสิบ', 'สี่สิบ', 'ห้าสิบ', 'หกสิบ', 'เจ็ดสิบ', 'แปดสิบ', 'เก้าสิบ')
denom = ('', 'สิบ', 'ร้อย', 'พัน', 'หมื่น', 'แสน', 'ล้าน', 'ล้าน',)

class ReportChequeBase(models.AbstractModel):
    _name = 'report.hdc_print_cheque.base'
    _description = 'Base Report Cheque'

    def _convert_nn(self, val):
            """convert a value < 10 to Thai.
            """
            if val < 10:
                return to_9[val >=0 and val or 0]
            for (dcap, dval) in ((k, 10 + (10 * v)) for (v, k) in enumerate(tens)):
                if dval + 10 > val:
                    if val % 10:
                        return dcap + (to_9[val % 10] == 'หนึ่ง' and 'เอ็ด' or to_9[val % 10])
                    return dcap
                
    def _convert_nnn(self, val):
        """
            convert a value < 1000 to english, special cased because it is the level that kicks 
            off the < 100 special case.  The rest are more general.  This also allows you to
            get strings in the form of 'forty-five hundred' if called directly.
        """
        word = ''
        (mod, rem) = (val % 1000000, val // 1000000)
        if rem > 0:
            word = self.thai_number(rem) + 'ล้าน'
        if mod > 0:
            word += self.thai_number(mod)
        return word
    
    def thai_number(self, val):
        if val < 100:
            return self._convert_nn(val)
        if val >= 1000000:
            return self._convert_nnn(val)
        for (didx, dval) in ((v - 1, 10 ** v) for v in range(len(denom))):
            if dval > val:
                mod = 10 ** didx
                l = val // mod
                r = val - (l * mod)
                ret = self._convert_nnn(l) + denom[didx]
                if r > 0:
                    ret = ret + self.thai_number(r)
                return ret
            
    def amount_to_text_th(self, number, currency='THB'):
        number = '%.2f' % number
        units_name = ''
        cents_name = ''
        list = str(number).split('.')
        start_word = self.thai_number(int(list[0]))
        end_word = self.thai_number(int(list[1]))
        if currency == 'THB':
            units_name = 'บาท'
            cents_name = 'สตางค์'
        if currency == 'JYP':
            units_name = 'เยน'
            cents_name = 'เซน'
        if currency == 'GBP':
            units_name = 'ปอนด์'
            cents_name = 'เพนนี'
        if currency == 'USD':
            units_name = 'ดอลล่าร์'
            cents_name = 'เซนต์'
        if currency == 'EUR':
            units_name = 'ยูโร'
            cents_name = 'เซนต์'

        if end_word == to_9[0]:
            return ''.join(filter(None, [start_word, units_name, (start_word or units_name) and (end_word or cents_name) and 'ถ้วน']))
        else:
            return ''.join(filter(None, [start_word, units_name, (start_word or units_name) and (end_word or cents_name) and ' ', end_word, cents_name]))

    @api.model
    def _get_report_values(self, docids, data=None):

        docs = self.env['pdc.wizard'].browse(docids)

        due_dates = {}

        for doc in docs:
            if doc.due_date:
                list_due_date = []
                due_date_str = str(doc.due_date)
                try:
                    due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d')
                    date = due_date_obj.strftime('%d')
                    month = due_date_obj.strftime('%m')
                    budda_year = int(due_date_obj.strftime('%Y')) + 543
                    new_due_date = date + month + str(budda_year)
                    list_due_date = list(new_due_date)
                    due_dates[doc.id] = list(new_due_date)
                    
                except:
                    print(f"------Invalid date format for {due_date_str}------")
                    continue

        report_values = {
            'doc_ids': docids,
            'doc_model': 'pdc.wizard',
            'docs': docs,
            'amount_to_text_th': self.amount_to_text_th,
            'due_dates': due_dates
        }

        return report_values



class ReportChequeTTB(ReportChequeBase):
    _name = 'report.hdc_print_cheque.report_cheque_ttb'
    _description = 'Report Cheque TTB'
    
class ReportChequeSCB(ReportChequeBase):
    _name = 'report.hdc_print_cheque.report_cheque_scb'
    _description = 'Report Cheque SCB'

class ReportChequeUOB(ReportChequeBase):
    _name = 'report.hdc_print_cheque.report_cheque_uob'
    _description = 'Report Cheque UOB'

class ReportChequeKBANK(ReportChequeBase):
    _name = 'report.hdc_print_cheque.report_cheque_kbank'
    _description = 'Report Cheque KBANK'

class ReportChequeLHB(ReportChequeBase):
    _name = 'report.hdc_print_cheque.report_cheque_lhb'
    _description = 'Report Cheque LHB'

class ReportChequeBBL(ReportChequeBase):
    _name = 'report.hdc_print_cheque.report_cheque_bbl'
    _description = 'Report Cheque BBL'   