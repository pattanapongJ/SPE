# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    etd_date = fields.Date(string='ETD Date')
    eta_date = fields.Date(string='ETA Date')
    wh_date = fields.Date(string='WH Date')
    deposit_detail = fields.Char(string='Deposit Detail')
    bl = fields.Char(string='BL')
    bl_date = fields.Date(string='BL date')
    awb_no = fields.Char(string='AWB No.')
    awb_date = fields.Date(string='AWB date')
    import_declaration = fields.Char(string='Import Declaration No.')
    import_declaration_date = fields.Date(string='Import Declaration date')
    duty_payment = fields.Char(string='Duty Payment No.')
    duty_payment_date = fields.Date(string='Duty Payment date')
    edt_from = fields.Char(string='E/D/T Form No.')
    edt_from_date = fields.Date(string='E/D/T From date')
    lc = fields.Char(string='LC')
    tt = fields.Char(string='TT')
    da = fields.Char(string='DA')
    dp_no = fields.Char(string='DP No.')
    wh_date = fields.Date(string='WH Date')
    country_orinal = fields.Many2one('res.country',string='Origin Country')
    remark_for_supplier = fields.Char(string='Remark For Supplier')
    internal_remark_purchase = fields.Char(string='Internal Remark Purchase')
    performa_invoice = fields.Char(string='Performa Invoice(PI)', tracking=True)
    performa_invoice_date = fields.Date(string='Performa Invoice Date', tracking=True)
    vendor_code = fields.Char(string='Vendor Code', related='partner_id.ref')
    confirm_po_user_id = fields.Many2one('res.users', string='Confirm PO by', store=True, tracking=True)
    confirm_po_status = fields.Selection(string="Confirm PO Status",
        selection=[
            ("inprogress", "In Progress"),
            ("confirm", "Confirmed"),
        ],readonly=True,default="inprogress",tracking=True,)
    
    commercial_invoice = fields.Char(string="Commercial Invoice (CI)", tracking=True)
    commercial_invoice_date = fields.Date(string="Commercial Invoice Date", tracking=True)
    free_text_commercial_invoice = fields.Char(string="Free Text Commercial Invoice")

    # @api.depends("partner_id")
    # def _compute_commercial_invoice(self):
    #     for recode in self:
    #         if recode.partner_id.parent_id:
    #             commercial_invoice = recode.partner_id.parent_id.name
    #         else:
    #             commercial_invoice = ''            
    #         recode.commercial_invoice = commercial_invoice

    
    @api.onchange('order_type')
    def _onchange_order_type(self):
        if self.order_type and self.order_type.journal_id and self.order_type.journal_id.branch_id:
            self.branch_id = self.order_type.journal_id.branch_id.id

        

    @api.model
    def create(self, vals):
        order_lines_vals = {}
        if vals.get('etd_date'):
            order_lines_vals['etd_date'] = vals.get('etd_date')
        if vals.get('eta_date'):
            order_lines_vals['eta_date'] = vals.get('eta_date')
        if vals.get('wh_date'):
            order_lines_vals['wh_date'] = vals.get('wh_date')

        res = super(PurchaseOrder, self).create(vals)

        if order_lines_vals:
            for order_line in res.order_line:
                order_line.write(order_lines_vals)

        return res

    def write(self, vals):
        order_lines_vals = {}
        if vals.get('etd_date'):
            order_lines_vals['etd_date'] = vals.get('etd_date')
        if vals.get('eta_date'):
            order_lines_vals['eta_date'] = vals.get('eta_date')
        if vals.get('wh_date'):
            order_lines_vals['wh_date'] = vals.get('wh_date')

        res = super(PurchaseOrder, self).write(vals)

        if order_lines_vals:
            for order in self:
                for order_line in order.order_line:
                    order_line.write(order_lines_vals)

        return res
    
    def confirm_po(self):
        self.confirm_po_user_id = self.env.user
        self.confirm_po_status = "confirm"

    def button_draft(self):
        res =  super(PurchaseOrder, self).button_draft()
        self.write({'confirm_po_user_id': False})
        self.write({'confirm_po_status': 'inprogress'})
        return res
    

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    etd_date = fields.Date(string='ETD Date',)
    eta_date = fields.Date(string='ETA Date',)
    wh_date = fields.Date(string='WH Date',)

