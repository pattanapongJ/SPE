# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.onchange("partner_id")
    def onchange_partner_id_contact(self):
        self.carrier_id = self.partner_id.carrier_id
        if self.partner_id.bank_ids:
            self.bank_account_id = self.partner_id.bank_ids[0]
        else:
            self.bank_account_id = False
        self.partner_group_id = self.partner_id.partner_group_id
        self.payment_method_id = self.partner_id.payment_method
        self.branch_no = self.partner_id.branch
        self.company_chain_id = self.partner_id.company_chain_id
        self.employee_id = self.partner_id.employee_id
        self.certificate_id = self.partner_id.certificate_id
        self.incoterm_id = self.partner_id.purchase_incoterm_id