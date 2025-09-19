# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ClaimProcessWizard(models.TransientModel):
    _inherit = 'claim.process.wizard'

    claim_modify_lines = fields.Many2one('claim.line.modify', "Claim Modify Line")

    @api.model
    def default_get(self, default_fields):
        """
        This method used to set a default value in the wizard.
        """
        res = super().default_get(default_fields)
        if self._context.get('active_model') == 'claim.line.modify':
            line = self.env['claim.line.modify'].search([('id', '=', self._context.get('active_id'))])
            res['claim_modify_lines'] = line.id
            res['state'] = line.claim_id.state
            # res['state'] = line.claim_id.state if line.claim_id else line.ticket_id.state
            res['product_id'] = line.to_be_replace_product_id.id or line.product_id.id
            res['quantity'] = line.to_be_replace_quantity or line.quantity
            res['is_create_invoice'] = line.is_create_invoice
        elif self._context.get('active_model') == 'crm.claim.ept':
            claim = self.env[self._context.get('active_model')].search([
                ('id', '=', self._context.get('active_id'))])
            res['picking_id'] = claim.return_picking_id.id if claim.return_picking_id else False
            if claim.return_picking_id:
                if claim.return_picking_id.state == 'cancel':
                    res['is_visible_goods_back'] = False
                else:
                    res['is_visible_goods_back'] = True
        else:
            line = self.env['claim.line.ept'].search([('id', '=', self._context.get('active_id'))])
            res['claim_line_id'] = line.id
            res['state'] = line.claim_id.state
            # res['state'] = line.claim_id.state if line.claim_id else line.ticket_id.state
            res['product_id'] = line.to_be_replace_product_id.id or line.product_id.id
            res['quantity'] = line.to_be_replace_quantity or line.quantity
            res['is_create_invoice'] = line.is_create_invoice
        return res

    def reject_claim(self):
        """reject claim with reason."""
        if  self.env.context.get('rma_type') == 'receive_modify':
            claim_modify_line_ids = self.env['claim.line.modify'].search([
                ('id', 'in', self.env.context.get('claim_modify_lines'))])
            if not claim_modify_line_ids:
                raise UserError(_('Claim Lines not found'))
            claim = claim_modify_line_ids[0].claim_id
            if claim.return_picking_id and claim.return_picking_id.state not in ['done', 'cancel']:
                raise UserError(_("Please first process Return Picking Order."))
            claim.write({'reject_message_id':self.reject_message_id.id, 'state':'reject'})
            return True
        return super(ClaimProcessWizard, self).reject_claim()

    def process_refund(self):
        """update replace product, qty and invoice on claim """
        if self._context.get('active_model') == 'claim.line.modify':
            if not self.claim_modify_lines:
                return False
            if self.claim_modify_lines.product_id == self.product_id:
                raise UserError(_("Please replace the product with other product, it seems\
                                like you replace with the same product."))
            self.claim_modify_lines.write({
                'to_be_replace_product_id':self.product_id.id,
                'to_be_replace_quantity':self.quantity,
                'is_create_invoice':self.is_create_invoice
            })
            return True
        return super(ClaimProcessWizard, self).process_refund()