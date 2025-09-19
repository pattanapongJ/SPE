
from odoo import api, fields, models

class AccountBilling(models.Model):
    _inherit = 'account.billing'
    
    sales_person_id = fields.Many2one('res.users', string='Salesperson', domain=[('sale_team_id', '!=', False)])
    percentage      = fields.Float(string='% (Percent)', default=100.0)
    branch_id = fields.Many2one('res.branch', string='Branch')
    
    def _filter_selected_invoices(self):
        existing_bills = self.env['account.billing'].search([("partner_id", "=", self.partner_id.id),("bill_type", "=", self.bill_type),('id', '!=', self._origin.id)])
        selected_invoice_ids = []
        
        for line in existing_bills:
            for inv in line.billing_line_ids:
                selected_invoice_ids.append(inv.invoice_id.id)
        return selected_invoice_ids
    
    def _get_invoices(self, date=False, types=False):   
        selected_invoice_ids = self._filter_selected_invoices()

        invoices = self.env["account.move"].search(
            [
                ("partner_id", "=", self.partner_id.id),
                ("state", "=", "posted"),
                ("payment_state", "!=", "paid"),
                ("currency_id", "=", self.currency_id.id),
                (date, "<=", self.threshold_date),
                ("move_type", "in", types),
                ('payment_state', '!=', 'reversed'),
                ('id', 'not in', selected_invoice_ids),
            ]
        )
        return invoices
    
    def _get_invoices_salesperson(self, date=False, types=False, start_date=False, end_date=False):
        selected_invoice_ids = self._filter_selected_invoices()
        
        domain = [
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'posted'),
                ('payment_state', '!=', 'paid'),
                ('currency_id', '=', self.currency_id.id),
                (date, '<=', self.threshold_date),
                ('move_type', 'in', types),
                ('payment_state', '!=', 'reversed'),
                ('id', 'not in', selected_invoice_ids),
                ('invoice_date', '>=', start_date),
                ('invoice_date', '<=', end_date),
            ]
        
        if self.sales_person_id:
            domain.append(('invoice_user_id', '=', self.sales_person_id.id))
            
        invoices = self.env['account.move'].search(domain)

        return invoices
    
    def _get_invoices_with_date(self, start_date=False, end_date=False, types=False):
        selected_invoice_ids = self._filter_selected_invoices()
        domain = [
                    ('partner_id', '=', self.partner_id.id),
                    ('state', '=', 'posted'),
                    ('payment_state', '!=', 'paid'),
                    ('currency_id', '=', self.currency_id.id),
                    ('invoice_date', '>=', start_date),
                    ('invoice_date', '<=', end_date),
                    ('move_type', 'in', types),
                    ('payment_state', '!=', 'reversed'),
                    ('id', 'not in', selected_invoice_ids),
                ]
        
        if self.sales_person_id:
            domain.append(
                ('invoice_user_id', '=', self.sales_person_id.id)
            )
        
        invoices = self.env["account.move"].search(domain)
        
        return invoices
    
    @api.onchange('sales_person_id')
    def _onchange_invoice_salesperson(self):
        self.billing_line_ids = False
        Billing_line = self.env["account.billing.line"]
        invoices = self.env["account.move"].browse(self._context.get("active_ids", []))
        if not invoices:
            types = ["in_invoice", "in_refund"]
            if self.bill_type == "out_invoice":
                types = ["out_invoice", "out_refund"]
            invoices = self._get_invoices_salesperson(self.threshold_date_type, types, self.start_date, self.end_date)
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
                    {
                        "invoice_id": line.id, 
                        "total": amount,
                        "amount_total": line.amount_total
                    }
                )
            
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
                    {
                        "invoice_id": line.id, 
                        "total": amount,
                        "amount_total": line.amount_total
                    }
                )
            
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
                    {
                        "invoice_id": line.id, 
                        "total": amount,
                        "amount_total": line.amount_total
                    }
                )
            
    def get_domain(self):
        selected_invoice_ids = self.billing_line_ids.mapped('invoice_id.id')

        if self.billing_line_ids.invoice_id:
                selected_invoice_ids += self.billing_line_ids.invoice_id.ids 
        domain = [
            ('partner_id', '=', self.partner_id.id),
            ('payment_state', '!=', 'paid'),
            ('state', '=', 'posted'),
            ('move_type', '=', self.bill_type),
            ('currency_id', '=', self.currency_id.id),
            ('id', 'not in', selected_invoice_ids),
            ('payment_state', '!=', 'reversed'),
        ]
        
        if self.sales_person_id:
            domain.append(('invoice_user_id', '=', self.sales_person_id.id))
        
        return domain
            
    
class AccountBillingLine(models.Model):
    _inherit = 'account.billing.line'
    
    amount_total = fields.Float(string='Total')
    percentage  = fields.Float(string='%', compute='_compute_percentage', store=True)
    bill_total  = fields.Float(string='Billing Total')
    bill_balance = fields.Float(string='Billing Balance')
    service     = fields.Char(string='Service')
    
    @api.depends('billing_id.percentage')
    def _compute_percentage(self):
        for rec in self:
            if rec.billing_id.percentage is not False:
                rec.percentage = rec.billing_id.percentage
                
                rec.bill_total = (rec.amount_total * (rec.percentage/100))
                
                if rec.total < 0:
                    rec.bill_balance = (rec.total + rec.bill_total)
                else:
                    rec.bill_balance = (rec.total - rec.bill_total)
                
        return True
    
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
                ('state', '=', 'posted'),
                ('move_type', '=', bill_type),
                ('currency_id', '=', active_bill.currency_id.id),
                ('id', 'not in', selected_invoice_ids),
                ('invoice_user_id', '=', active_bill.sales_person_id.id),
                ('payment_state', '!=', 'reversed'),
            ]
            
        amount = self.invoice_id.amount_residual
        if self.invoice_id.move_type in ["out_refund", "in_refund"]:
            amount *= (-1)
        self.total = amount

        self.amount_total = self.invoice_id.amount_total
        
        self._compute_percentage()
            
        return {'domain': {'invoice_id': domain}}