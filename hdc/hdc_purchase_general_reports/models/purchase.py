from odoo import fields, models,api, _
from odoo.exceptions import UserError
class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    contact_person = fields.Many2one('res.partner', string = 'Contact Person', readonly = False)
    delivery_terms = fields.Many2one(
        'account.incoterms', string='Delivery Terms',tracking=True
    )
    
    approve_order = fields.Char(string='')
    order_plan = fields.Char(string='')

    
    total_amount = fields.Float(
        string="Total Amount",
        compute="_compute_total_amount",
        store=True, 
    )
    
    total_amount_vat = fields.Float(
        string="Total Amount Vat",
        compute="_compute_total_amount_vat",
        store=True, 
    )
    
    def check_iso_name(self, check_iso):
        for purchase in self:
            check_model = self.env["ir.actions.report"].search([('model', '=', 'purchase.order'),('report_name', '=', check_iso)], limit=1)
            if check_model:
                return check_model.iso_name
            else:
                return "-"

    @api.onchange('partner_id')
    def _domain_contact_person(self):
        if self.partner_id:
            self.contact_person = False
            return {"domain": {
                "contact_person": [('type', '=', "contact"),
                               ('id', '=', self.partner_id.child_ids.ids)],
            }}
        else:
            self.contact_person = False
            return {
                "domain": {
                    "contact_person": [('type', '=', "contact")],
                    }
                }
            
    @api.depends("order_line")
    def _compute_total_amount_vat(self):
        for order in self:
            total_multi_disc_amount = 0.0
            for line in order.order_line:
                total_multi_disc_amount += line.multi_disc_amount

            order.total_amount_vat = total_multi_disc_amount

            # total = sum(
            #     line.product_qty * line.price_unit
            #     for line in order.order_line
            # )
            # if total:
            #     total_vat = sum(
            #         total * (line.discount / 100) 
            #         for line in order.order_line
            #     )
            #     order.total_amount_vat = total_vat
            
    @api.depends("order_line")
    def _compute_total_amount(self):
        for order in self:
            total = sum(
                line.product_qty * line.price_unit
                for line in order.order_line
            )
            order.total_amount = total
                
            
    def print_po_and_rfq(self):
        if len(self.branch_id) == 0:
            raise UserError(
                        _(
                            "กรุณาระบุ Branch"
                        )
                    )

        self.ensure_one()
        return {
                "name": "Report",
                "type": "ir.actions.act_window",
                "res_model": "wizard.purchase.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_state": self.state},

            }
        
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    description_purchase = fields.Char(string="Description Purchase")   
    
    @api.depends('product_qty', 'price_unit')
    def _compute_total_amount(self):
        for line in self:
            line.total_amount = line.product_qty * line.price_unit
        
class PurchaseRequest(models.Model):

    _inherit = "purchase.request"

    purchase_request_id = fields.Many2one('purchase.request', string='PRQ') 
    total_product_qty = fields.Float(
        string="Total Product Quantity",
    )

    def action_print_request(self):
        return self.env.ref('hdc_purchase_general_reports.purchase_request_report_view').report_action(self.purchase_request_id)
    
    def check_iso_name(self, check_iso):
        for purchase in self:
            check_model = self.env["ir.actions.report"].search([('model', '=', 'purchase.request'),('report_name', '=', check_iso)], limit=1)
            if check_model:
                return check_model.iso_name
            else:
                return "-"
    
class PurchaseRequestLine(models.Model):

    _inherit = "purchase.request.line"

    pending_order = fields.Float(string="Pending QTY", compute="_compute_pending_order")
    order_plan = fields.Float(string='Order Plan', compute="_compute_order_plan")
    approve_order = fields.Char(string='Approve Order')

    converted_qty = fields.Float('Converted Quantity', compute='_compute_converted_qty')

    @api.depends('product_qty', 'product_uom_id')
    def _compute_converted_qty(self):
        for record in self:
            if record.product_uom_id.id != record.product_id.uom_id.id:
                record.converted_qty = record.product_uom_id._compute_quantity(record.product_qty, record.product_id.uom_id)
            else:
                record.converted_qty = record.product_qty  

    @api.onchange('product_id', 'request_id.line_ids', 'request_id.total_product_qty', 'product_qty')
    def _compute_pending_order(self):
        for line in self:
            line.pending_order = 0.00
            if line.product_id:
                # product_search = self.env["product.product"].search([("id", "=", self.product_id.id)])
                product_search = self.env["product.product"].browse(line.product_id.id)
                if product_search:
                    line.pending_order = product_search.incoming_qty

    @api.onchange('product_id', 'request_id.line_ids', 'request_id.total_product_qty', 'product_qty')
    def _compute_order_plan(self):
        for line in self:
            line.order_plan = 0.00
            if line.product_id:
                line.order_plan = line.product_qty
            

                    