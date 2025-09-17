# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api,fields, models
from datetime import date, timedelta

class Quotations(models.Model):
    _inherit = 'quotation.order'

    is_credit_limit = fields.Boolean(related='type_id.is_credit_limit',string="Check Credit Limit")
    
    @api.onchange('partner_id')
    def onchange_partner_id_check_credit_limit(self):
        customer_credit_id = self.env["customer.credit.limit"].search([('partner_id', '=', self.partner_id.id)])
        if customer_credit_id.credit_id.credit_line:
            credit_line = customer_credit_id.credit_id.credit_line
            if len(credit_line) > 0:
                self.team_id = credit_line[0].sale_team_id
                self.user_id = credit_line[0].sale_user_id
                
        if self.partner_id.credit_limit_on_hold == True:
            return {
                    'warning': {'title': "Customer On Hold", 
                                'message': 
                                "Customer have been on hold. Please contact administration for further guidance"
                                },
                }
        
        if customer_credit_id:
            credit_team_remain = 0
            sale_team_id = False
            if customer_credit_id:
                sale_team_id = customer_credit_id.credit_id.credit_line.filtered(lambda l: l.sale_team_id == self.team_id)
                if sale_team_id:
                    credit_team_remain = sale_team_id.credit_remain

            if customer_credit_id.cash_remain <= 0 or credit_team_remain <= 0:
                partner_id = self.partner_id

                exceeded_amount_team = credit_team_remain - self.amount_total
                exceeded_amount_team = "{:.2f}".format(exceeded_amount_team)
                exceeded_amount_team = float(exceeded_amount_team)
                
                return {
                    'warning': {'title': "Credit Limit Warning", 
                                'message': 
                                "Customer: %s \nCredit Remain: %.2f  \nCash Limit: %.2f \nExceeded Amount (Credit): %.2f "  
                                % (partner_id.name, credit_team_remain ,partner_id.cash_limit ,exceeded_amount_team),
                                },
                }
            
    @api.onchange('payment_term_id')
    def _onchange_payment_term_id_change_validity_date(self):
        if self.payment_term_id and self.payment_term_id.days:
            self.validity_date = date.today() + timedelta(days=self.payment_term_id.days)