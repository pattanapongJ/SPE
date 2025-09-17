# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta
import re

class AccountMove(models.Model):
    _inherit = "account.move"

    def get_type_partner_id(self, group_acc_id):
        return group_acc_id
        
    def get_type_partner_name(self, group_acc_id):
        return group_acc_id
    
    def get_value_debit(self, debit):
        return debit
           
    def get_value_credit(self, credit):
        return credit
    
    def get_currency_rate(self):

        if self.date:
            currency_rate = self.currency_id.rate_ids

            # Found Match
            for cur in currency_rate:
                if self.date == cur.name:
                    return cur.rate
                    
            # Not Found Match
            list_date = []

            for cur in currency_rate:
                cur_date = cur.name
                date_string = cur_date.strftime('%Y-%m-%d')
                list_date.append(date_string)
                
            list_date.sort(reverse=True)

            for date in list_date:
                date_in_list = datetime.strptime(date, '%Y-%m-%d').date()
                if self.date >= date_in_list:
                    rate_value = self.env['res.currency.rate'].search([('name','=',date_in_list)])
                    return rate_value.rate
        else:
            return ''