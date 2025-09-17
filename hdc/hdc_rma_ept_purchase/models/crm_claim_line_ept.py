# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class CRMClaimLine(models.Model):
    _name = 'purchase.claim.line.ept'
    _description = 'CRM Claim Line Purchase'

    is_create_invoice = fields.Boolean("Create Invoice", copy=False)
    quantity = fields.Float('Return Quantity', copy=False)
    done_qty = fields.Float('Delivered Quantity', compute='_compute_get_done_quantity')
    return_qty = fields.Float('Received Quantity', compute='_compute_return_quantity')
    to_be_replace_quantity = fields.Float("Replace Quantity", copy=False)

    rel_is_rma_without_receipt = fields.Boolean(related='purchase_claim_id.is_rma_without_receipt', store=True)

    claim_type = fields.Selection([
        ('refund', 'Refund'),
        ('replace_same_product', 'Replace With Same Product'),
        ('replace_other_product', 'Replace With Other Product')]
        , string="Action", copy=False, compute='_compute_claim_type',
                                  store=True)

    product_id = fields.Many2one('product.product', string='Product')
    product_id_no_r = fields.Many2one('product.product', string='Product')
    product_id_r = fields.Many2one('product.product', string='Product')
    purchase_claim_id = fields.Many2one('purchase.crm.claim.ept', string='Related claim', copy=False,
                               ondelete='cascade')
    to_be_replace_product_id = fields.Many2one('product.product', string="Product to be Replace",
                                               copy=False)
    move_id = fields.Many2one('stock.move')
    rma_reason_id = fields.Many2one('purchase.rma.reason.ept', string="Customer Reason")
    serial_lot_ids = fields.Many2many('stock.production.lot', string="Lot/Serial Number")
    return_total = fields.Float('Returned total')
    remark = fields.Text('Remark')

    @api.model
    def create(self, vals):
        record = super(CRMClaimLine, self).create(vals)
        previous_claimline_ids = self.env['purchase.claim.line.ept'].search([('id', '!=', record.id),
                                                                        ('move_id', '=', record.move_id.id),
                                                                        ('product_id', '=', record.move_id.product_id.id)])
        if previous_claimline_ids:
            returned_qty = 0
            for line_id in previous_claimline_ids:
                returned_qty += line_id.quantity
            if returned_qty < record.move_id.quantity_done:
                qty = record.move_id.quantity_done - returned_qty
                if qty > 0:
                    record.return_total = returned_qty
        return record

    def _compute_return_quantity(self):
        """
        This method used to set a return quantity in the claim line base on the return move.
        """
        for record in self:
            record.return_qty = 0
            if record.purchase_claim_id.return_picking_id:
                move_line = record.purchase_claim_id.return_picking_id.mapped('move_lines') \
                    .filtered(lambda r: r.sale_line_id.id == record.move_id.sale_line_id.id and \
                                       r.product_id.id == record.product_id.id and \
                                       r.origin_returned_move_id.id == record.move_id.id)
                record.return_qty = move_line.quantity_done

    def _compute_get_done_quantity(self):
        """
        This method used to set done qty in claim line base on the delivered picking qty.
        """
        for record in self:
            record.done_qty = record.move_id.quantity_done

    @api.depends('rma_reason_id')
    def _compute_claim_type(self):
        """
        This method used to set action based on customer's reason.
        """
        for record in self:
            record.claim_type = record.rma_reason_id.action

    @api.onchange('serial_lot_ids')
    def onchange_serial_lot_id(self):
        """
        This method used for validation.
        """
        if self.purchase_claim_id:
            if self.quantity < len(self.serial_lot_ids.ids):
                raise UserError(
                    _("Lenth of Lot/Serial number are greater then the Return Quantity !"
                      "\n Please set the proper Lot/Serial Number"))

    @api.onchange('rma_reason_id')
    def onchange_product_id(self):
        """
        This method used recommendation to users.
        """
        warning = False
        if self.rma_reason_id and self.rma_reason_id.action == 'repair' \
                and self.purchase_claim_id.is_rma_without_incoming:
            warning_msg = {
                'title':_('Recommendation'),
                'message':"We recommend if you select repair action then we will need "
                          "return shipment."

                          "It will not create a return delivery of the repair order."
            }

            warning = {'warning':warning_msg}

        return warning

    def unlink(self):
        """
        This method used to delete the claim line when clam state in draft
        otherwise it will give a warning message.
        """
        if self.filtered(lambda l: l.purchase_claim_id and l.purchase_claim_id.state != 'draft'):
            raise UserError(_("Claim Line cannot be delete once it Approved."))
        return super().unlink()

    def action_claim_refund_process_ept(self):
        """
        This action used to return the product from the claim line base on return action.
        """
        return {
            'name':'Return Products',
            'type':'ir.actions.act_window',
            'view_mode':'form',
            'res_model':'purchase.claim.process.wizard',
            'src_model':'purchase.claim.line.ept',
            'target':'new',
            'context':{'product_id':self.product_id.id, 'hide':True, 'claim_line_id':self.id}
        }

    @api.constrains('quantity')
    def check_qty(self):
        for line in self:
            if line.quantity < 0:
                raise UserError(_('Quantity must be positive number'))

            is_rma_without_receipt = line.purchase_claim_id.is_rma_without_receipt
            if not is_rma_without_receipt:
                if line.quantity > line.move_id.quantity_done:
                    raise UserError(_('Quantity must be less than or equal to the delivered quantity'))
                

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.product_id_r = rec.product_id # for first time default value

    @api.onchange('product_id_r')
    def _onchange_product_id_r(self):
        for rec in self:
            if rec.product_id_r:
                rec.product_id = rec.product_id_r # for second if product_id_r change value

    @api.onchange('product_id_no_r')
    def _onchange_product_id_no_r(self):
        for rec in self:
            if rec.product_id_no_r:
                rec.product_id = rec.product_id_no_r
