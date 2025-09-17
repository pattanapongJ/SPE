# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context

class CRMClaimLine(models.Model):
    _inherit = 'claim.line.ept'
    _description = 'CRM Claim Line'

    description = fields.Char(string="Description")

    def check_qty(self):
        """
        This method is used to check claim line's quantity
        """
        if self.rma_type == 'receive_modify':
            pass
        else: 
            return super(CRMClaimLine, self).check_qty()

class ModifyClaimLine(models.Model):
    _name = 'claim.line.modify'
    _description = 'Modify Claim Line'

    description = fields.Char(string="Description",required=True)
    is_create_invoice = fields.Boolean("Create Invoice", copy=False)
    quantity = fields.Float('Return Quantity', copy=False)
    done_qty = fields.Float('Delivered Quantity', compute='_compute_get_done_quantity')
    done_qty_update = fields.Float('Delivered Quantity update')
    return_qty = fields.Float('Received Quantity', compute='_compute_return_quantity')
    to_be_replace_quantity = fields.Float("Replace Quantity", copy=False)

    claim_type = fields.Selection([
        ('refund', 'Refund'),
        ('replace_same_product', 'Replace With Same Product'),
        ('replace_other_product', 'Replace With Other Product'),
        ('repair', 'Repair')], string="Action", copy=False, compute='_compute_claim_type',
                                  store=True)

    product_id = fields.Many2one('product.product', string='Product')
    claim_id = fields.Many2one('crm.claim.ept', string='Related claim', copy=False,
                               ondelete='cascade')
    to_be_replace_product_id = fields.Many2one('product.product', string="Product to be Replace",
                                               copy=False)
    move_id = fields.Many2one('stock.move')
    rma_reason_id = fields.Many2one('rma.reason.ept', related='claim_id.rma_reason_id', string="Customer Reason")
    serial_lot_ids = fields.Many2many('stock.production.lot', string="Lot/Serial Number")


    def _compute_get_done_quantity(self):
        """
        This method used to set done qty in claim line base on the delivered picking qty.
        """
        for record in self:
            if record.done_qty_update > 0:
                record.done_qty = record.done_qty_update
            else:
                record.done_qty = record.move_id.quantity_done

    def _compute_return_quantity(self):
        """
        This method used to set a return quantity in the claim line base on the return move.
        """
        for record in self:
            record.return_qty = 0
            if record.claim_id.return_picking_id:
                move_line = record.claim_id.return_picking_id.mapped('move_lines') \
                    .filtered(lambda r:r.product_id.id == record.product_id.id and r.description_picking == record.description and r.state == "done")
                record.return_qty = move_line.quantity_done

    @api.depends('rma_reason_id')
    def _compute_claim_type(self):
        """
        This method used to set action based on customer's reason.
        """
        for record in self:
            record.claim_type = record.rma_reason_id.action
    
    def action_claim_refund_process_ept(self):
        """
        This action used to return the product from the claim line base on return action.
        """
        return {
            'name':'Return Products',
            'type':'ir.actions.act_window',
            'view_mode':'form',
            'res_model':'claim.process.wizard',
            'src_model':'claim.line.ept',
            'target':'new',
            'context':{'product_id':self.product_id.id, 'hide':True, 'claim_modify_lines':self.id}
        }
    def _prepare_invoice_line(self):
        self.ensure_one()
        res = {
            'name': self.product_id.display_name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_id.uom_id.id,
            'quantity': self.quantity,
            'price_unit': self.product_id.lst_price,
            'analytic_account_id':  False,
        }
        return res