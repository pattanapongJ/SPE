# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class CRMClaimRejectMessage(models.Model):
    _name = 'purchase.claim.reject.message'
    _description = 'CRM Claim Reject Message Purchase'

    name = fields.Char("Reject Reason", required=1)

class CRMReason(models.Model):
    _name = 'purchase.rma.reason.ept'
    _description = 'CRM Reason Purchase'

    name = fields.Char("RMA Reason", required=1)
    action = fields.Selection([
        ('refund', 'Refund'),
        ('replace_same_product', 'Replace With Same Product'),
        ('replace_other_product', 'Replace With Other Product')], string="Related Action", required=1)
    journal_id = fields.Many2one('account.journal', domain=[("type", "=", "purchase"),("show_in_credit_note", "=", True)], string='Credit Note Journal')