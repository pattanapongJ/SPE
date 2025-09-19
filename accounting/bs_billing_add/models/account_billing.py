from odoo import api,fields, models, _
from odoo.exceptions import UserError

class AccountBillings(models.Model):
    _inherit = 'account.billing'
    
    total_bill_amount = fields.Float(string='Total', compute='_compute_amount',store=True)
    start_date        = fields.Date(string='Start Invoice Date', default=lambda self: fields.Date.context_today(self))
    end_date          = fields.Date(string='End Invoice Date', default=lambda self: fields.Date.context_today(self))
    payment_terms_id  = fields.Many2one('account.payment.term', string='Payment Terms')

    @api.depends('billing_line_ids')
    def _compute_amount(self):
        bills = self.env['account.billing'].search([])
        for rec in bills:
            rec.total_bill_amount = sum(float(line['total']) for line in rec.billing_line_ids)
            
    @api.onchange("partner_id", "currency_id", "threshold_date", "threshold_date_type")
    def _onchange_invoice_list(self):
        self.billing_line_ids = False
        Billing_line = self.env["account.billing.line"]
        invoices = self.env["account.move"].browse(self._context.get("active_ids", []))
        if not invoices:
            types = ["in_invoice", "in_refund"]
            if self.bill_type == "out_invoice":
                types = ["out_invoice", "out_refund"]
            invoices = self._get_invoices(self.threshold_date_type, types)
        else:
            if invoices[0].move_type in ["out_invoice", "out_refund"]:
                self.bill_type = "out_invoice"
            else:
                self.bill_type = "in_invoice"
        for line in invoices:
            amount = line.amount_residual
            if line.move_type in ["out_refund", "in_refund"]:
                amount *= (-1)
            self.billing_line_ids += Billing_line.new(
                    {"invoice_id": line.id, "total": amount}
                )
            
    # override
    def _get_invoices(self, date=False, types=False):        
        invoices = self.env["account.move"].search(
            [
                ("partner_id", "=", self.partner_id.id),
                ("state", "=", "posted"),
                ("payment_state", "!=", "paid"),
                ("currency_id", "=", self.currency_id.id),
                (date, "<=", self.threshold_date),
                ("move_type", "in", types),
                ('payment_state', '!=', 'reversed'),
            ]
        )
        return invoices
            
    def _get_invoices_with_date(self, start_date=False, end_date=False, types=False):
        invoices = self.env["account.move"].search(
            [
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'posted'),
                ('payment_state', '!=', "paid"),
                ('currency_id', '=', self.currency_id.id),
                ('invoice_date', '>=', start_date),
                ('invoice_date', '<=', end_date),
                ('move_type', 'in', types),
            ]
        )
        return invoices

    @api.onchange('start_date', 'end_date')
    def _onchange_date_range(self):
        self.billing_line_ids = False
        Billing_line = self.env["account.billing.line"]
        invoices = self.env["account.move"].browse(self._context.get("active_ids", []))
        if not invoices:
            types = ["in_invoice", "in_refund"]
            if self.bill_type == "out_invoice":
                types = ["out_invoice", "out_refund"]
            invoices = self._get_invoices_with_date(self.start_date, self.end_date, types)
        else:
            if invoices[0].move_type in ["out_invoice", "out_refund"]:
                self.bill_type = "out_invoice"
            else:
                self.bill_type = "in_invoice"
        for line in invoices:
            amount = line.amount_residual
            if line.move_type in ["out_refund", "in_refund"]:
                amount *= (-1)
            self.billing_line_ids += Billing_line.new(
                    {"invoice_id": line.id, "total": amount}
                )
            
    def unlink(self):
        for record in self:
            if record.state == 'billed':
                raise UserError("You cannot delete a record that is billed.")
        return super(AccountBillings, self).unlink()
    
    @api.onchange('partner_id')
    def _onchange_partner(self):
        if not self.payment_terms_id:
            if self.bill_type == 'out_invoice':
                self.payment_terms_id = self.partner_id.property_payment_term_id
            else:
                self.payment_terms_id = self.partner_id.property_supplier_payment_term_id
    
    def get_domain(self):
        selected_invoice_ids = self.billing_line_ids.mapped('invoice_id.id')

        if self.billing_line_ids.invoice_id:
                selected_invoice_ids += self.billing_line_ids.invoice_id.ids 
        domain = [
            ('partner_id', '=', self.partner_id.id),
            ('payment_state', '!=', 'paid'),
            ('payment_state', '!=', 'reversed'),
            ('state', '=', 'posted'),
            ('move_type', '=', self.bill_type),
            ('currency_id', '=', self.currency_id.id),
            ('id', 'not in', selected_invoice_ids)
        ]
        
        return domain
    
    @api.model
    def create(self, vals):
        res = super(AccountBillings, self).create(vals)
        for line in res.billing_line_ids:
            if line.invoice_date is False:
                line.unlink()
        return res
    
    # override
    def write(self, vals):
        res = super(AccountBillings, self).write(vals)
        for line in self.billing_line_ids:
            if line.invoice_date is False:
                line.unlink()
        return res
          
class AccountBillingLine(models.Model):
    _inherit = 'account.billing.line'
    
    @api.onchange('invoice_id')
    def _get_invoice_domain(self): 
        domain = []
        active_bill_id = self.billing_id._origin.id or self.billing_id.id
        if not active_bill_id:
            domain = self.billing_id.get_domain()
        else:
            # current active bill
            active_bill = self.billing_id

            bill_type = active_bill.bill_type
            partner_id = active_bill.partner_id.id
            
            selected_invoice_ids = active_bill.billing_line_ids.mapped('invoice_id.id')

            if self.invoice_id:
                selected_invoice_ids += self.invoice_id.ids
            
            domain = [
                ('partner_id', '=', partner_id),
                ('payment_state', '!=', 'paid'),
                ('payment_state', '!=', 'reversed'),
                ('state', '=', 'posted'),
                ('move_type', '=', bill_type),
                ('currency_id', '=', active_bill.currency_id.id),
                ('id', 'not in', selected_invoice_ids)
            ]
            
        amount = self.invoice_id.amount_residual
        if self.invoice_id.move_type in ["out_refund", "in_refund"]:
            amount *= (-1)
        self.total = amount
            
        return {'domain': {'invoice_id': domain}}
