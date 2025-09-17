# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

class WizardUpdateCommissionCode(models.TransientModel):
    _name = 'wizard.update.commission.code'
    _description = "Wizard to mark as done or create back order"

    update_commission_code_id = fields.Many2one('update.commission.code', string = 'Update Commission Code')
    commission_code = fields.Many2many('commission.type', string = 'Commission Code')
    commission_remarks = fields.Char(string='Commission Remarks')
    invoice_lines = fields.One2many('wizard.update.commission.code.invoice.line', 'wizard_update_commission_code_id', string = 'Invoice Lists')
    selected = fields.Boolean(string = "Select All",default=True)

    @api.onchange('selected')
    def _selected_onchange(self):
        if self.selected:
            for line in self.invoice_lines:
                line.selected = True
        else:
            for line in self.invoice_lines:
                line.selected = False

    def action_update_commission_code(self):
        for line in self.invoice_lines:
            if line.selected == True:
                line.invoice_line_id.update({"commission_code": self.commission_code, "commission_remarks": self.commission_remarks})
        

class WizardUpdateCommissionCodeInvoiceLine(models.TransientModel):
    _name = "wizard.update.commission.code.invoice.line"
    _description = "Wizard Update Commission Code Invoice Line"

    wizard_update_commission_code_id = fields.Many2one('wizard.update.commission.code', string = 'Wizard Update Commission Code')
    selected = fields.Boolean(string="Select")
    commission_code = fields.Many2many('commission.type', string = 'Commission Code')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    invoice_line_id = fields.Many2one('account.move.line', string='Invoice Line')
    invoice_id_date = fields.Date(string = "INV Date")
    form_no = fields.Char(string="SPE Invoice")
    partner_id = fields.Many2one('res.partner', string = 'ลูกค้า')
    product_id = fields.Many2one('product.product', string='สินค้า')
    quantity = fields.Float(string='Quantity',)
    product_uom_id = fields.Many2one('uom.uom', string='UOM')
    price_unit = fields.Float(string='Price',digits='Product Price')
    triple_discount = fields.Char('Discount',)
    price_subtotal = fields.Monetary(string='Subtotal', store=True, readonly=True,currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency',)