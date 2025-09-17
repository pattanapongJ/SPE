# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta

class AccountMove(models.Model):
    _inherit = "account.move"

    receipts_bill = fields.Char(string="Receipts Bill")
    receipts_date = fields.Datetime(string="Receipts Date", default=False)
    is_tms = fields.Boolean('To TMS')
    transport_line_id = fields.Many2one('delivery.round', string="สายส่ง TRL")
    company_round_id = fields.Many2one('company.delivery.round', string="Mode of delivery")
    transport_desc = fields.Char(related='transport_line_id.code',string="สายส่ง TRL Description")
    company_round_desc = fields.Char(related='company_round_id.code',string="Mode of delivery Description")
    to_finance = fields.Boolean('To Finance')
    tms_remark = fields.Char('TMS Remark')
    cancel_remark = fields.Char('Cancel Remark')
    logistics_user_id = fields.Many2one('res.users', string = "Logistics Operator", copy=False)
    delivery_date = fields.Date(string = "Delivery Date", readonly = True)

    delivery_status = fields.Selection([
        ('sending', 'Sending'),
        ('resend', 'Resend'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled'),
    ], string="Delivery Status", compute="_compute_delivery_status", store=True, readonly=False,)
    billing_status = fields.Selection([
        ('none', 'None'),
        ('to_billing', 'To Billing'),
        ('billing', 'Billing'),
        ('to_finance', 'To Finance'),
        ('finance', 'Finance'),
        ('close', 'Closed'),
    ], string="Billing Status", default="none")
    finance_type = fields.Selection([
        ('cash', 'เงินสด/โอน/เช็ค'),
        ('urgent', 'ด่วนการเงิน'),
    ], string="Finance Type")

    def validate_billing_finance(self):
        for record in self:
            update = {}     
            if not record.to_finance:
                update['to_finance'] = True
            if not record.receipts_bill:
                update['receipts_bill'] = self.env.user.name
            if not record.receipts_date:
                update['receipts_date'] = datetime.today()
            record.write(update)

    @api.onchange('to_finance')
    def _onchange_to_finance(self):
        self.receipts_bill = self.env.user.name
        self.receipts_date = datetime.today()


    def force_update_status(self, delivery_status=None, billing_status=None):
        """
        Force update delivery_status and billing_status regardless of invoice state
        This method bypasses normal field constraints and updates status directly
        """
        if not self.exists():
            return
            
        # Validate status values
        valid_delivery_statuses = ['sending', 'resend', 'completed', 'cancel']
        valid_billing_statuses = ['none', 'to_billing', 'billing', 'to_finance', 'finance', 'close']
        
        update_fields = []
        update_values = []
        
        if delivery_status is not None:
            if delivery_status in valid_delivery_statuses:
                update_fields.append('delivery_status = %s')
                update_values.append(delivery_status)
            else:
                raise UserError(_("Invalid delivery_status: %s. Valid values are: %s") % 
                              (delivery_status, ', '.join(valid_delivery_statuses)))
                
        if billing_status is not None:
            if billing_status in valid_billing_statuses:
                update_fields.append('billing_status = %s')
                update_values.append(billing_status)
            else:
                raise UserError(_("Invalid billing_status: %s. Valid values are: %s") % 
                              (billing_status, ', '.join(valid_billing_statuses)))
            
        if update_fields:
            # Add invoice ID to values
            update_values.append(self.id)
            
            # Use SQL update to bypass ORM constraints and field restrictions
            sql_query = """
                UPDATE account_move 
                SET {fields}
                WHERE id = %s
            """.format(fields=', '.join(update_fields))
            
            try:
                self.env.cr.execute(sql_query, update_values)
                # Invalidate cache to ensure updated values are reflected
                self.invalidate_cache(['delivery_status', 'billing_status'])
                
                # Log the update for audit trail
                _logger = self.env['ir.logging']
                _logger.sudo().create({
                    'name': 'TMS Status Update',
                    'level': 'INFO',
                    'message': 'Updated invoice %s status: delivery_status=%s, billing_status=%s' % 
                              (self.name, delivery_status, billing_status),
                    'func': 'force_update_status',
                    'line': 0,
                    'path': 'hdc_tms.models.account_move',
                    'type': 'server',
                })
                
            except Exception as e:
                raise UserError(_("Error updating invoice status: %s") % str(e))

    @api.depends("to_finance")
    def _compute_delivery_status(self):
        for rec in self:
            if not rec.billing_status:
                rec.billing_status = 'none'
            if rec.to_finance:
                if rec.billing_status == 'to_billing':
                    rec.billing_status = 'billing'
                if rec.billing_status == 'to_finance':
                    rec.billing_status = 'finance'
            else:
                if rec.billing_status == 'billing':
                    rec.billing_status = 'to_billing'
                if rec.billing_status == 'finance':
                    rec.billing_status = 'to_finance'