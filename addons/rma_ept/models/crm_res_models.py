# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

class CRMClaimRejectMessage(models.Model):
    _name = 'claim.reject.message'
    _description = 'CRM Claim Reject Message'

    name = fields.Char("Reject Reason", required=1)

class CRMReason(models.Model):
    _name = 'rma.reason.ept'
    _description = 'CRM Reason'

    name = fields.Char("RMA Reason", required=1)
    action = fields.Selection([
        ('refund', 'Refund'),
        ('replace_same_product', 'Replace With Same Product'),
        ('replace_other_product', 'Replace With Other Product'),
        ('repair', 'Repair')], string="Related Action", required=1)

    is_not_receipt = fields.Boolean(string="Not receipt", default=False)
    journal_id = fields.Many2one('account.journal', domain=[("type", "=", "sale"),("show_in_credit_note", "=", True)], string='Credit Note Journal')
    remark = fields.Text('Remark')
    
    @api.model
    def _get_domain_picking_type_id_rg(self):
        addition_operation_type = self.env["addition.operation.type"].search([("code", "=", "AO-08")], limit=1)
        picking_type_id = self.env['stock.picking.type'].search([("addition_operation_types", "=", addition_operation_type.id)])
        return [('id','in',picking_type_id.ids)]
    @api.model
    def _get_domain_picking_type_id(self):
        addition_operation_type = self.env["addition.operation.type"].search([("code", "=", "AO-05")], limit=1)
        picking_type_id = self.env['stock.picking.type'].search([("addition_operation_types", "=", addition_operation_type.id)])
        return [('id','in',picking_type_id.ids)]

    operation_type_rg_id = fields.Many2one('stock.picking.type', string='Operation Type RG',
                                        domain=lambda self: self._get_domain_picking_type_id_rg(),
                                        help="Operation Type for RG location")

    operation_type_id = fields.Many2one('stock.picking.type', string='Operation Type',
                                        domain="[('code','=','incoming')]",
                                        help="Operation Type for Return location, if not Select Invoice,will use Operation Type")
    operation_type_delivery_id = fields.Many2one('stock.picking.type', string='Operation Type Delivery',
                                        domain="[('code', '=', 'outgoing')]",
                                        help="Operation Type for Delivery location, if not Select Invoice,will use Operation Type")
        