# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)
import math
import re
import time

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError, Warning
import odoo.addons.decimal_precision as dp
import warnings

#-------------------------------------------------------------
#THAI
#-------------------------------------------------------------

to_9 = ('ศูนย์', 'หนึ่ง', 'สอง', 'สาม', 'สี่', 'ห้า', 'หก', 'เจ็ด', 'แปด', 'เก้า' )
tens = ('สิบ', 'ยี่สิบ', 'สามสิบ', 'สี่สิบ', 'ห้าสิบ', 'หกสิบ', 'เจ็ดสิบ', 'แปดสิบ', 'เก้าสิบ')
denom = ('', 'สิบ', 'ร้อย', 'พัน', 'หมื่น', 'แสน', 'ล้าน', 'ล้าน',)

to_9_en = ('Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine')
tens_en = ('Ten', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety')
denom_en = ('', 'Ten', 'Hundred', 'Thousand', 'Ten Thousand', 'Hundred Thousand', 'Million', 'Million',)


class Currency(models.Model):
    _inherit = "res.currency"

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

    def amount_to_text_th(self, number, currency):
        number = '%.2f' % number
        units_name = 'บาท'
        cents_name = 'สตางค์'
        list = str(number).split('.')
        start_word = self.thai_number(int(list[0]))
        end_word = self.thai_number(int(list[1]))
        cents_number = int(list[1])
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


    def _convert_nn_en(self, val):
        """Convert a value < 10 to English."""
        if val < 10:
            return to_9_en[val >= 0 and val or 0]
        for (dcap, dval) in ((k, 10 + (10 * v)) for (v, k) in enumerate(tens_en)):
            if dval + 10 > val:
                if val % 10:
                    return dcap + (to_9_en[val % 10] == 'One' and 'One' or to_9_en[val % 10])
                return dcap

    def _convert_nnn_en(self, val):
        """
        Convert a value < 1000 to English, specially cased because it is the level that kicks 
        off the < 100 special case. The rest are more general. This also allows you to
        get strings in the form of 'forty-five hundred' if called directly.
        """
        word = ''
        (mod, rem) = (val % 1000000, val // 1000000)
        if rem > 0:
            word = self.english_number(rem) + ' Million '
        if mod > 0:
            word += self.english_number(mod)
        return word

    def english_number(self, val):
        if val < 100:
            return self._convert_nn_en(val)
        if val >= 1000000:
            return self._convert_nnn_en(val)
        for (didx, dval) in ((v - 1, 10 ** v) for v in range(len(denom_en))):
            if dval > val:
                mod = 10 ** didx
                l = val // mod
                r = val - (l * mod)
                ret = self._convert_nnn_en(l) + denom_en[didx]
                if r > 0:
                    ret = ret + self.english_number(r)
                return ret

    def amount_to_text_en(self, number, currency):
        number = '%.2f' % number
        units_name = 'Dollar'
        cents_name = 'Cents'
        list = str(number).split('.')
        start_word = self.english_number(int(list[0]))
        end_word = self.english_number(int(list[1]))
        cents_number = int(list[1])
        if currency == 'Baht':
            units_name = 'Baht'
            cents_name = 'Satang'
        if currency == 'JYP':
            units_name = 'Yen'
            cents_name = 'Sen'
        if currency == 'GBP':
            units_name = 'Pound'
            cents_name = 'Pence'
        if currency == 'USD':
            units_name = 'Dollar'
            cents_name = 'Cent'
        if currency == 'EUR':
            units_name = 'Euro'
            cents_name = 'Cent'

        if end_word == to_9_en[0]:
            return ''.join(filter(None, [start_word, units_name, (start_word or units_name) and (end_word or cents_name) and 'Whole']))
        else:
            return ''.join(filter(None, [start_word, units_name, (start_word or units_name) and ' ', end_word, cents_name]))

    #-------------------------------------------------------------
    # Generic functions
    #-------------------------------------------------------------

    _translate_funcs = {'th' : amount_to_text_th}

    def amount_to_text(self, amount):
        amount_words = super(Currency, self).amount_to_text(amount)
        # lang_code = self.env.context.get('lang') or self.env.user.lang
        # lang = self.env['res.lang'].search([('code', '=', lang_code)])
        # if lang not in self._translate_funcs:
        #     _logger.warning(_("no translation function found for lang: '%s'"), lang)
        #     #TODO: (default should be th) same as above
        #     lang = 'th'
        # amount_words = self.amount_to_text_th(abs(amount), self.currency_unit_label)
        return amount_words
    
    def amount_to_text_eng(self, amount):
        amount_words = super(Currency, self).amount_to_text(amount)
        return amount_words