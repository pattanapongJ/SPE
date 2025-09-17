from odoo import models, fields, api
from num2words import num2words


class print_check(models.AbstractModel):
    _name = 'report.bs_pdc.report_pdc_wizard_view'
    _description = 'Print cheque From PDC'

    def get_date(self, date):
        if date:
            date = date.strftime("%Y-%m-%d")
            date = date.split('-')
            return date
        return ''

    def get_partner_name(self, obj, p_text):
        if p_text and obj.partner_text:
            if p_text == 'prefix':
                return obj.partner_text + ' ' + obj.partner_id.name
            else:
                return obj.partner_id.name + ' ' + obj.partner_text

        return obj.partner_id.name

    def amount_word(self, obj):
        amt = str(obj.payment_amount)
        amt_lst = amt.split('.')
        if obj.partner_id and obj.partner_id.lang:
            amt_word = num2words(int(amt_lst[0]), lang=obj.partner_id.lang)
        else:
            amt_word = num2words(int(amt_lst[0]))
        lst = amt_word.split(' ')
        if float(amt_lst[1]) > 0:
            lst.append(' and ' + amt_lst[1] + ' / ' + str(100))
        lst.append('only')
        lst_len = len(lst)
        lst_len = len(lst)
        first_line = ''
        second_line = ''
        for l in range(0, lst_len):
            if lst[l] != 'euro':
                if obj.cheque_formate_id.word_in_f_line >= l:
                    if first_line:
                        first_line = first_line + ' ' + lst[l]
                    else:
                        first_line = lst[l]
                else:
                    if second_line:
                        second_line = second_line + ' ' + lst[l]
                    else:
                        second_line = lst[l]

        if obj.cheque_formate_id.is_star_word:
            first_line = '***' + first_line
            if second_line:
                second_line += '***'
            else:
                first_line = first_line + '***'

        first_line = first_line.replace(",", "")
        second_line = second_line.replace(",", "")
        return [first_line, second_line]

    def get_footer_text(self, footer_text, cheque_num):
        if footer_text and cheque_num:
            return str(footer_text) + ' ' + str(cheque_num)

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['pdc.wizard'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'pdc.wizard',
            'docs': docs,
            'get_date': self.get_date,
            'get_partner_name': self.get_partner_name,
            'amount_word': self.amount_word,
            'get_footer_text': self.get_footer_text,
        }