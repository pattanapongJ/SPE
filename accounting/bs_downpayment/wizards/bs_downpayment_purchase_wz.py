# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BSDownpaymentPurchaseWizard(models.TransientModel):
    _name = 'bs.downpayment.purchase.wz'
    _description = _('Link Purchase and Down Payment')

    downpayment_id = fields.Many2one('bs.downpayment',string='Down Payment',required=True,readonly=True)
    line_ids = fields.One2many('bs.downpayment.purchase.wz.line','wizard_id',string='Order List')
    remaining_amount = fields.Float(string='Remaining Balance',compute='_compute_remaining_balance')
    partner_id = fields.Many2one(related='downpayment_id.partner_id')
    currency_id = fields.Many2one(related='downpayment_id.currency_id')
    
    
    @api.model
    def default_get(self, fields_list):
        res= super().default_get(fields_list)
        if res.get('downpayment_id'):
            downpayment = self.env['bs.downpayment'].browse(res.get('downpayment_id'))
            applied_amount = sum(line.price_unit for line in downpayment.purchase_order_lines.filtered(lambda x:x.state in ('done','purchase')))
            remaining_amount = downpayment.amount - applied_amount
            if not remaining_amount:
                raise ValidationError("There is no remaining balance")
        return res
    
    @api.constrains("line_ids", "remaining_amount")
    def _check_deduction_amount(self):
        for rec in self:
            if rec.remaining_amount < 0:
                applied_amount = sum(line.price_unit for line in rec.downpayment_id.purchase_order_lines.filtered(lambda x:x.state in ('done','purchase')))
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
            applied_amount = sum(line.price_unit for line in rec.downpayment_id.purchase_order_lines.filtered(lambda x:x.state in ('done','purchase')))
            current_amount = sum(line.amount for line in rec.line_ids)
            rec.remaining_amount = rec.downpayment_id.amount - (applied_amount + current_amount)
            
        
class BSDownpaymentPurchaseWizardLine(models.TransientModel):
    _name = 'bs.downpayment.purchase.wz.line'
    _description = _('Link Purchase and Down Payment Line')

    wizard_id = fields.Many2one('bs.downpayment.purchase.wz',required=True)
    order_id = fields.Many2one('purchase.order',string='Purchase Order',required=True)
    amount = fields.Float(string='Amount')
    
    
    def create_order_line(self,downpayment):
        self.ensure_one()
        if not downpayment.move_ids.invoice_line_ids:
            return
        invoice_line = downpayment.move_ids.invoice_line_ids[0]
        order_val = self._prepare_po_line(downpayment,invoice_line)
        order_line = self.env['purchase.order.line'].sudo().create(order_val)
        invoice_line.write({'purchase_line_id':[(4,order_line.id)]})


    def _prepare_po_line(self,downpayment,invoice_line):
        context = {'lang':downpayment.partner_id.lang}
        po_values = {
            'name': invoice_line.name,
            'gross_unit_price': self.amount,
            'product_uom_qty': 0.0,
            'order_id': self.order_id.id,
            'bs_downpayment_id':downpayment.id,
            'product_uom': downpayment.product_id.uom_id.id,
            'product_id': downpayment.product_id.id,
            'taxes_id': [(6, 0, invoice_line.tax_ids.ids)],
            'is_deposit': True,
            'sequence': self.order_id.order_line and self.order_id.order_line[-1].sequence + 1 or 10,
        }
        del context
        return po_values
