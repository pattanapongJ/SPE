from odoo import api, fields, models, _


class AccountBilling(models.Model):
    _inherit = 'account.billing'

    billing_history_ids = fields.One2many('billing.history', 'billing_id', string="Billing History")

    @api.onchange('bill_type')
    def _onchange_bill_type(self):
        if self.bill_type in ['out_invoice']:
            return {'domain': {'partner_id': [('customer', '=', True)]}}
        if self.bill_type in ['in_invoice']:
            return {'domain': {'partner_id': [('supplier', '=', True)]}}
        else:
            return {'domain': {'partner_id': []}}

class BillingHistory(models.Model):
    _name = 'billing.history'
    _description = 'Billing History'

    billing_id = fields.Many2one('account.billing', string="Related Billing", required=True, ondelete='cascade')
    date = fields.Date(string="Date", default=fields.Date.today, required=True)
    # create_by = fields.Many2one('res.users', string="Created By", default=lambda self: self.env.user, readonly=True)
    description = fields.Char(string="Description")