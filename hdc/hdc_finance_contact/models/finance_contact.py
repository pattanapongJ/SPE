from odoo import api, fields, models, _
from datetime import datetime


class BillingFinanceContact(models.Model):
    _inherit = 'account.billing'

    billing_remark = fields.Char(string="Billing Remark")
    responsible_id = fields.Many2one('res.users', string="Responsible")
    finance_contact_id = fields.Many2one('finance.contact', string="Finance Contact")

    @api.model
    def create(self, vals):
        """Set default value for Finance Contact based on Partner"""
        if 'finance_contact_id' not in vals and 'partner_id' in vals:
            partner = self.env['res.partner'].browse(vals['partner_id'])
            if partner.finance_contact_id:
                vals['finance_contact_id'] = partner.finance_contact_id.id
        return super(BillingFinanceContact, self).create(vals)

class PartnerFinanceContact(models.Model):
    _inherit = 'res.partner'

    finance_contact_id = fields.Many2one("finance.contact", string="Finance Contact")

class FinanceContact(models.Model):
    _name = 'finance.contact'
    _description = 'Finance Contact'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    description = fields.Char(string='Description')