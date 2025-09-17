# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
class CrmClaimEpt(models.Model):
    _inherit = "crm.claim.ept"
    _description = 'RMA CRM Claim'

    is_dewalt = fields.Boolean(string='Dewalt',default=False)
    
    # spe_invoice = fields.Char(string='SPE Invoice')
    spe_invoice = fields.Many2one(
        'account.move',
        string="SPE Invoice",
        domain="[('id', 'in', available_invoice_ids), ('state', '=', 'posted')]"
    )
    
    available_invoice_ids = fields.Many2many(
        'account.move',
        compute='_compute_available_invoices',
        store=False
    )

    warranty_type = fields.Selection(
            selection=  [
                            ('under', 'Under Warranty'),
                            ('out', 'Out of Warranty'),
                            ('none', 'None'),
                        ],
        string='Warranty Expiration',default='none',
    )
    
    @api.onchange('rma_type')
    def _onchange_rma_type(self):
        if self.rma_type != 'receive_modify':
            self.is_dewalt = False
            
    @api.onchange('rma_reason_id')
    def _onchange_rma_reason_id(self):
        if self.rma_reason_id and self.is_dewalt:
            self.picking_type_id = self.rma_reason_id.operation_type_id.id
    
    @api.depends('account_id', 'spe_invoice')
    def _compute_available_invoices(self):
        for rec in self:
            domain = [('form_no', '!=', False)]
            if rec.account_id:
                domain = ['|'] + domain + [
                    ('id', '=', rec.account_id.id),
                    ('old_spe_invoice', '=', rec.account_id.form_no),
                ]
            elif rec.spe_invoice:
                domain = ['|'] + domain + [
                    ('form_no', '=', rec.spe_invoice.form_no),
                    ('old_spe_invoice', '=', rec.spe_invoice.form_no),
                ]
            rec.available_invoice_ids = self.env['account.move'].search(domain).ids
    
    @api.onchange('account_id')
    def _onchange_account_id_sync_spe_invoice(self):
        if self.account_id:
            spe_invoice = self.env['account.move'].search([
                '&',
                ('state', '=', 'posted'),('reversed_entry_id', '=', False),
                '|',
                ('form_no', '=', self.account_id.form_no),
                ('old_spe_invoice', '=', self.account_id.form_no),
            ], limit=1)

            if spe_invoice:
                self.spe_invoice = spe_invoice

            return {
                'domain': {
                    'spe_invoice': [
                        '&', ('state', '=', 'posted'),('reversed_entry_id', '=', False),
                        '|',
                        ('form_no', '=', self.account_id.form_no),
                        ('old_spe_invoice', '=', self.account_id.form_no),
                    ]
                }
            }
        else:
            self.spe_invoice = False
            return {
                'domain': {
                    'spe_invoice': [
                        ('form_no', '!=', False),
                        ('state', '=', 'posted'),('reversed_entry_id', '=', False),
                        
                        
                    ]
                }
            }

    @api.onchange('spe_invoice')
    def _onchange_spe_invoice_sync_account_id(self):
        if self.spe_invoice:
            self.account_id = self.spe_invoice.id
            domain = [
                '&',
                ('id', 'in', self.invoice_ids.ids),
                '&',
                ('state', '=', 'posted'),('reversed_entry_id', '=', False),
                '|',
                ('form_no', '=', self.spe_invoice.form_no),
                ('old_spe_invoice', '=', self.spe_invoice.form_no),
            ]
        else:
            self.account_id = False
            domain = [
                ('id', 'in', self.invoice_ids.ids),
                ('state', '=', 'posted'),('reversed_entry_id', '=', False),
            ]

        return {
            'domain': {
                'account_id': domain
            }
        }

    @api.onchange('is_dewalt')
    def _onchange_is_dewalt(self):
        """
        Update rma_reason_id when is_dewalt is changed.
        """
        if self.is_dewalt:
            self.rma_reason_id = self.env['rma.reason.ept'].search(
                [('action', '=', 'repair')], order='id desc', limit=1
            )
            if self.rma_reason_id:
                self.picking_type_id = self.rma_reason_id.operation_type_id.id if self.rma_reason_id.operation_type_id else False

    @api.onchange('account_id')
    def onchange_account_id(self):
        if self.is_dewalt:
            sale_id = self.env['sale.order'].search(
                [('invoice_ids', '=', self.account_id.id)], limit = 1)
            if sale_id:
                self.email_from = sale_id.partner_id.email
                self.partner_id = sale_id.partner_id.id
                self.partner_delivery_id = sale_id.partner_shipping_id.id
                self.return_partner_delivery_id = sale_id.partner_shipping_id.id
            return
        return super().onchange_account_id()
    
    def approve_claim(self):
        if self.warranty_type == 'none':
            raise UserError(_("Please select Warranty Expiration."))
        res = super().approve_claim()
        return res