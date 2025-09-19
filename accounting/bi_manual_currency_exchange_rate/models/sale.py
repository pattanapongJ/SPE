# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _
from odoo.exceptions import Warning

class SaleOrder(models.Model):
    _inherit ='sale.order'
    
    sale_manual_currency_rate_active = fields.Boolean('Apply Manual Exchange')
    sale_manual_currency_rate = fields.Float('Rate', digits=0)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def product_id_change(self):
        result = super().product_id_change()
        if self.order_id.sale_manual_currency_rate_active:
            company = self.order_id.company_id
            currency_rate = self.order_id.sale_manual_currency_rate/company.currency_id.rate
            price_unit = self.product_id.lst_price
            manual_currency_rate = price_unit * currency_rate            
            self.update({'price_unit':manual_currency_rate})

        return result


    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        super().product_uom_change
        if self.order_id.sale_manual_currency_rate_active:
            company = self.order_id.company_id
            currency_rate = self.order_id.sale_manual_currency_rate/company.currency_id.rate
            price_unit = self.product_id.lst_price
            manual_currency_rate = price_unit * currency_rate
            self.price_unit = manual_currency_rate
        

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _create_invoice(self, order, so_line, amount):
        res = super(SaleAdvancePaymentInv,self)._create_invoice(order, so_line, amount)
        if order.sale_manual_currency_rate_active:
            res.write({'manual_currency_rate_active':order.sale_manual_currency_rate_active,'manual_currency_rate':order.sale_manual_currency_rate})
        return res

class SaleOrder(models.Model):
    _inherit = "sale.order"

    # def _create_invoices(self, grouped=False, final=False):
    #     res = super(SaleOrder,self)._create_invoices(grouped=grouped, final=final)
    #     invoice_obj = self.env['account.move'].browse(res.id)
    #     if self.sale_manual_currency_rate_active:
    #         invoice_obj.write({'manual_currency_rate_active':self.sale_manual_currency_rate_active,'manual_currency_rate':self.sale_manual_currency_rate})
    #     return invoice_obj

    def _prepare_invoice(self):
        _invoice_value = super(SaleOrder, self)._prepare_invoice()
        _invoice_value.update({
            'manual_currency_rate_active': self.sale_manual_currency_rate_active,
            'manual_currency_rate': self.sale_manual_currency_rate
        })
        return _invoice_value


