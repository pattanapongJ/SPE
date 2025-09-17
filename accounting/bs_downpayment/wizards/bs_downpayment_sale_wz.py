# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class BSDownpaymentSaleWizard(models.TransientModel):
    _name = 'bs.downpayment.sale.wz'
    _description = _('Link Sale and Down Payment')

    downpayment_id = fields.Many2one('bs.downpayment',string='Down Payment',required=True,readonly=True)
    line_ids = fields.One2many('bs.downpayment.sale.wz.line','wizard_id',string='Order List')
    remaining_amount = fields.Float(string='Remaining Balance',compute='_compute_remaining_balance')
    partner_id = fields.Many2one(related='downpayment_id.partner_id')
    currency_id = fields.Many2one(related='downpayment_id.currency_id')
    
    
    @api.model
    def default_get(self, fields_list):
        res= super().default_get(fields_list)
        if res.get('downpayment_id'):
            downpayment = self.env['bs.downpayment'].browse(res.get('downpayment_id'))
            applied_amount = sum(line.price_unit for line in downpayment.sale_order_lines.filtered(lambda x:x.state in ('done','sale')))
            remaining_amount = downpayment.amount - applied_amount
            if not remaining_amount:
                raise ValidationError("There is no remaining balance")
        return res
    
    @api.constrains("line_ids", "remaining_amount")
    def _check_deduction_amount(self):
        for rec in self:
            if rec.remaining_amount < 0:
                applied_amount = sum(line.price_unit for line in rec.downpayment_id.sale_order_lines.filtered(lambda x:x.state in ('done','sale')))
                remaining_amount = rec.downpayment_id.amount - applied_amount
                raise UserError( _("The total downpayment should be %s") % remaining_amount)
        
    

    def action_apply(self):
        for line in self.line_ids:
            if line.amount == 0:
                continue
            line.create_order_line(self.downpayment_id)
        
    
    
    @api.depends('downpayment_id','line_ids.amount')
    def _compute_remaining_balance(self):
        for rec in self:
            applied_amount = sum(line.price_unit for line in rec.downpayment_id.sale_order_lines.filtered(lambda x:x.state in ('done','sale')))
            current_amount = sum(line.amount for line in rec.line_ids)
            rec.remaining_amount = rec.downpayment_id.amount - (applied_amount + current_amount)
            
        
    
    
    
        




class BSDownpaymentSaleWizardLine(models.TransientModel):
    _name = 'bs.downpayment.sale.wz.line'
    _description = _('Link Sale and Down Payment Line')
    
    wizard_id = fields.Many2one('bs.downpayment.sale.wz',required=True)
    order_id = fields.Many2one('sale.order',string='Sale Order',required=True)
    amount = fields.Float(string='Amount')
    
    
    def create_order_line(self,downpayment):
        self.ensure_one()
        if not downpayment.move_ids.invoice_line_ids:
            return
        invoice_line = downpayment.move_ids.invoice_line_ids[0]
        order_val = self._prepare_so_line(downpayment,invoice_line)
        order_line = self.env['sale.order.line'].sudo().create(order_val)
        invoice_line.write({'sale_line_ids':[(4,order_line.id)]})
    
    
    def _prepare_so_line(self,downpayment,invoice_line):
        context = {'lang':downpayment.partner_id.lang}
        so_values = {
            'name': invoice_line.name,
            'price_unit': self.amount,
            'product_uom_qty': 0.0,
            'order_id': self.order_id.id,
            'discount': 0.0,
            'bs_downpayment_id':downpayment.id,
            'product_uom': downpayment.product_id.uom_id.id,
            'product_id': downpayment.product_id.id,
            'tax_id': [(6, 0, invoice_line.tax_ids.ids)],
            'is_downpayment': True,
            'sequence': self.order_id.order_line and self.order_id.order_line[-1].sequence + 1 or 10,
        }
        del context
        return so_values
