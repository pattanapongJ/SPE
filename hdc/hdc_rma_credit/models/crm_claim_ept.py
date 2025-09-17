# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from unittest import result
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context

class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    picking_id = fields.Many2one('stock.picking', 'picking Order')

class CRMReason(models.Model):
    _inherit = "rma.reason.ept"

    is_select_product_receipt = fields.Boolean(string="Modern Trade", default=False)

    @api.onchange('is_select_product_receipt')
    def _onchange_is_select_product_receipt(self):
        if self.is_select_product_receipt:
            self.action = 'refund'

class CrmClaimEpt(models.Model):
    _inherit = "crm.claim.ept"
    _description = 'RMA CRM Claim'

    is_job_no = fields.Char(string="Job No.")

    is_select_product_receipt = fields.Boolean(related='rma_reason_id.is_select_product_receipt',string="Modern Trade", store=True)
    claim_line_create_ids = fields.One2many("claim.line.ept", "claim_id", string="Return Line")
    picking_id = fields.Many2one('stock.picking', string='Delivery Order', copy=False)

    @api.onchange('picking_id')
    def onchange_picking_id(self):
        if self.is_select_product_receipt:
            return
        else :
            return super(CrmClaimEpt, self).onchange_picking_id()

    def approve_claim(self):
        """
        This method used to approve the RMA. It will create a return
        picking base on the RMA configuration.
        """
        if self.is_select_product_receipt or self.return_request_id:
            warehouse_id = self.picking_id.picking_type_id.warehouse_id.id
            check_addition_operation_type = self.env['addition.operation.type'].search(
                [('code', '=', "AO-05")], limit=1
            )
            check_return_customer = self.env['stock.picking.type'].search(
                [('addition_operation_types', '=', check_addition_operation_type.id) , ('warehouse_id', '=', warehouse_id)], limit=1
            )
            if self.return_request_id:
                # warehouse_id = self.return_request_id.picking_type_id.warehouse_id.id
                # check_addition_operation_type = self.env['addition.operation.type'].search(
                #     [('code', '=', "AO-08")], limit=1
                # )
                check_return_customer = self.rma_reason_id.operation_type_rg_id
                if check_return_customer:
                    warehouse_id = check_return_customer.warehouse_id.id
                else:
                    raise UserError(_("Operation Type Return Customer is not set"))

        

            if not check_return_customer:
                raise UserError(_("Please Check Operation Type Return Customer"))
            if len(self.claim_line_ids) <= 0:
                raise UserError(_("Please set return products."))

            procurement_group = self.env['procurement.group'].create({
                'name': self.code,
                'move_type': 'direct',
                'picking_id':self.picking_id.id,
                'partner_id':self.partner_delivery_id.id,
            })
            new_picking = self.env['stock.picking'].create({
                        'partner_id': self.partner_id.id,
                        'picking_type_id': check_return_customer.id,
                        'state': 'draft',
                        'claim_id':self.id,
                        'origin': self.code,
                        'location_id': check_return_customer.default_location_src_id.id,
                        'location_dest_id': check_return_customer.default_location_dest_id.id,
                        'group_id': procurement_group.id,
                        })

            for line in self.claim_line_ids:
                move = self.env['stock.move'].create({
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': check_return_customer.default_location_src_id.id,
                    'location_dest_id': check_return_customer.default_location_dest_id.id,
                    'picking_id': new_picking.id,
                    'origin': self.code,
                    'state': 'draft',
                    'company_id': check_return_customer.company_id.id,
                })
                line.move_id = move.id

            self.return_picking_id = new_picking.id
            if self.is_not_receipt:
                refund_lines, do_lines, so_lines, ro_lines = self.prepare_list_based_on_line_operations()
                if refund_lines:
                    # aaa=self.create_credit_notes(refund_lines)
                    self.create_refund(refund_lines)
                if do_lines:
                    self.create_do(do_lines)
                if so_lines:
                    self.create_so(so_lines)
                if ro_lines:
                    self.create_ro(ro_lines)

                self.write({'state':'process'})
            else:
                self.write({'state':'approve'})
            if self.claim_type == 'replace_other_product':
                self.sudo().action_create_po()
            self.sudo().action_rma_send_email()
        else:
            return super(CrmClaimEpt, self).approve_claim()

    def create_refund(self, claim_lines):
        if self.is_select_product_receipt or not self.picking_id:
            return self.create_credit_notes(claim_lines)
        else:
            return super(CrmClaimEpt, self).create_refund(claim_lines)
    def create_credit_notes(self,refund_lines):
        if not refund_lines:
            raise UserError(_('No refund lines found to create Credit Note.'))

        # ดึงข้อมูลจาก refund_lines
        invoice_lines = []
        for line in refund_lines:
            invoice_lines.append(
                (0, 0, line._prepare_invoice_line()),
            )

        # สร้าง Credit Note
        credit_note_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_refund',
            'invoice_line_ids': invoice_lines,
            'invoice_origin': self.name,
            'claim_id':self.id,
            'original_value':self.original_value,
            'register_date':self.register_date,
            'is_job_no':self.is_job_no,
            'customer_requisition':self.customer_requisition,
            'customer_ref':self.customer_ref,
            'invoice_user_employee_id':self.sale_person_employee_id.id if self.sale_person_employee_id else False,
        }
        if self.spe_invoice_no:
            credit_note_vals['old_spe_invoice'] = self.spe_invoice_no
        if self.rma_reason_journal_id:
            credit_note_vals['journal_id'] = self.rma_reason_journal_id.id
        
        credit_note = self.env['account.move'].create(credit_note_vals)
        if credit_note:
            self.write({'refund_invoice_ids': [(4, credit_note.id)]})

        return credit_note

    def set_to_draft(self):
        """This method used to set claim into the draft state."""
        result = super(CrmClaimEpt,self).set_to_draft()
        if self.to_return_picking_ids:
            # if self.to_return_picking_ids.filtered(lambda r: r.state in ['cancel', 'done']):
            #     raise UserError(_("Claim cannot be move draft state once "
            #                       "it Receipt is done or cancel."))
            for picking in self.to_return_picking_ids.filtered(lambda r: r.state not in ['cancel', 'done']):
                if picking.state == 'assigned':
                    picking.do_unreserve()
                picking.action_cancel()

        return result
    
        

