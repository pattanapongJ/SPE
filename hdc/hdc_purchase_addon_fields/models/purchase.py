# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    customer = fields.Char(string='Customer')
    carrier_id = fields.Many2one("delivery.carrier", string="Delivery Mode")

    line_count = fields.Integer(
        string="Purchase Request Line count",
        compute="_compute_line_count",
        readonly=True,
    )
    bank_account_id = fields.Many2one('res.partner.bank',string="Recipenit Bank")
    partner_group_id = fields.Many2one('partner.group', string='Partner Group')
    payment_method_id = fields.Many2one('account.payment.method', string = 'Payment Method')
    branch_no = fields.Char(string='Branch No',)
    company_chain_id = fields.Many2one('company.chain',string='Company Chain')
    partner_invoice_id = fields.Many2one('res.partner', string = 'Bill Address')
    employee_id = fields.Many2one("hr.employee", string="Employee")
    shipper = fields.Char(string='Shipper',)
    spot_rate = fields.Float(string="Spot Rate",default=0.0,)

    po_reference = fields.Char(string="PO Reference")

    @api.depends("order_line")
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.mapped("order_line"))

    def action_view_purchase_request_line(self):
        action = self.env.ref(
            "purchase_request.purchase_request_line_form_action"
        ).read()[0]
        # lines = self.mapped("order_line")
        # if len(lines) > 1:
        #     action["domain"] = [("id", "in", lines.ids)]
        # elif lines:
        #     action["views"] = [
        #         (self.env.ref("purchase_request.purchase_request_line_form").id, "form")
        #     ]
        #     action["res_id"] = lines.ids[0]
        return action
    
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    spot_rate = fields.Float(string="Spot Rate",default= 0.0,)
    requisition = fields.Char(related='order_id.requisition_id.name', string="Purchase Agreement", store=True)
    po_reference = fields.Char(related='order_id.po_reference',string="PO Reference",store=True)
    partner_ref = fields.Char(related='order_id.partner_ref',string="Vendor Reference",store=True)
    
    @api.model
    def default_get(self, fields):
        rec = super().default_get(fields)
        if self.order_id:
            self.update({
                'spot_rate': self.order_id.spot_rate
            })
        return rec
    
    remark_1 = fields.Char(string="Remark 1")
    remark_2 = fields.Char(string="Remark 2")
    last_supplier_id = fields.Many2one(related="product_id.last_purchase_supplier_id", string="Last Supplier")
    last_supplier_date = fields.Datetime(related="product_id.last_purchase_date", string="Last Supplier Date")
    last_purchase_price = fields.Float(related="product_id.last_purchase_price", string="Last Purchase Price")
    last_purchase_date = fields.Datetime(related="product_id.last_purchase_date", string="Last Purchase Date")

    # gross_unit_price = fields.Float(string = "Gross Unit Price", required = True, digits='Purchase Order',default=lambda self: self._default_gross_unit_price())
    
    # @api.model
    # def _default_gross_unit_price(self):
    #     price_unit = self.env.context.get('price_unit')
    #     product_id = self.env.context.get('product_id')
    #     print("price_unit", price_unit)
    #     print("product_id", product_id)
    #     asset_id = self.env.context.get("active_id")
    #     asset = self.env["purchase.order.line"].browse(asset_id)

    #     print("asset", asset)

    #     if price_unit:
    #         return price_unit
    #     return 0.0