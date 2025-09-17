# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context

class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    picking_id = fields.Many2one('stock.picking', 'picking Order')

class CrmClaimEpt(models.Model):
    _inherit = "crm.claim.ept"
    _description = 'RMA CRM Claim'

    rma_type_selection = [
        ('receive', 'รับสินค้าคืน'),
        ('receive_modify', 'รับสินค้าส่งซ่อม'),
    ]

    rma_type = fields.Selection(
        selection=rma_type_selection,
        string='RMA Type',
        required=True,
        default='receive',
    )

    picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Return Operation",
        domain="[('addition_operation_types.code', '=', 'AO-05')]",
    )

    claim_modify_line_ids = fields.One2many("claim.line.modify", "claim_id", string="Return Line")
    is_claim_supplier = fields.Boolean('เคลม Supplier')
    claim_supplier = fields.Char('Supplier')
    is_not_claim = fields.Boolean('ไม่เคลม')
    is_cn = fields.Boolean('CN')
    claim_qty = fields.Float('Quantity')
    claim_date = fields.Date('Date')
    claim_doc_no = fields.Char('Doc No.')
    claim_remark = fields.Text('Remark')
    
    @api.onchange('rma_type')
    def onchange_rma_type(self):
        for rma in self:
            if rma.rma_type == 'receive':
                rma.account_id = False
                rma.partner_id = False
                rma.partner_phone = False
                rma.email_from = False
                rma.sale_id = False
                rma.section_id = False
                rma.partner_delivery_id = False
                rma.return_partner_delivery_id = False
                if rma.claim_modify_line_ids:
                    rma.claim_modify_line_ids = False
            else:
                if rma.claim_line_ids:
                    rma.claim_line_ids = False

    @api.onchange('partner_id')
    def _get_domain_onchange_partner_id(self):
        res = {}
        if self.partner_id.phone:
            self.partner_phone = self.partner_id.phone
        
        child_id = self.env['res.partner'].search([('type', '=', 'delivery'),('id', 'in', self.partner_id.child_ids.ids)])
        if child_id:
            self.partner_delivery_id = child_id[0].id
            self.return_partner_delivery_id = child_id[0].id
            partner_shipping_id = ['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id),('id', 'in', self.partner_id.child_ids.ids), ('type', '=', 'delivery')]
        else:
            partner_shipping_id = ['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id),
                                ('id', 'in', [self.partner_id.id])]
            self.partner_delivery_id = self.partner_id.id
            self.return_partner_delivery_id =  self.partner_id.id
        res['domain'] = {'partner_delivery_id': partner_shipping_id, 'return_partner_delivery_id': partner_shipping_id}
        return res


    def create_return_picking_modify(self, claim_lines=False):
        """
        This method used to create a return picking, when the approve button clicks on the RMA.
        """
        return_picking_id = True
        location_id = self.location_id.id
        

        vals = {'picking_id':self.return_picking_id.id if claim_lines else self.picking_id.id, 'remark': "RETURN SALE RMA"}
        active_id = self.return_picking_id.id if claim_lines else self.picking_id.id
        return_picking_wizard = self.env['stock.return.picking'].with_context \
            (active_id=active_id).create(vals)
        return_picking_wizard._onchange_picking_id()
        if location_id and not claim_lines:
            return_picking_wizard.write({'location_id':location_id})

        return_lines = self.create_return_picking_lines(claim_lines, return_picking_wizard)
        return_picking_wizard.write({'product_return_moves':[(6, 0, return_lines)]})
        new_picking_id, pick_type_id = return_picking_wizard._create_rma_returns()
        if claim_lines:
            self.write({'to_return_picking_ids':[(4, new_picking_id)]})
        else:
            return_picking_id = self.create_move_lines(new_picking_id)       
    
        if location_id:
            self.set_as_internal_picking(location_id, claim_lines, new_picking_id)
        return return_picking_id

    def _prepare_procurement_group_vals(self):
        """prepare a procurement group vals."""
        if self.rma_type == 'receive_modify':
            return {
                'name':self.code,
                'partner_id':self.partner_delivery_id.id,
                'picking_id':self.picking_id.id,
                'move_type': 'direct',
            }
        else:
            return {
                'name':self.code,
                'partner_id':self.partner_delivery_id.id,
                'sale_id':self.sale_id.id,
                'move_type':self.sale_id.picking_policy or 'direct',
            }
    def create_do_modify(self, claim_lines):

        """based on this method to create a picking one..two or three step."""
        procurement_group = self.env['procurement.group'].create({
                'name': self.code,
                'move_type': 'direct',  # หรือ 'pull' ตามกรณี
                'picking_id':self.picking_id.id,
                'partner_id':self.partner_delivery_id.id,
            })
        new_picking = self.env['stock.picking'].create({
                        'partner_id': self.partner_id.id,
                        'picking_type_id': self.picking_type_id.return_picking_type_id.id,
                        'state': 'draft',
                        'claim_id':self.id,
                        'origin': self.code,
                        'location_id': self.picking_type_id.return_picking_type_id.default_location_src_id.id or self.picking_type_id.return_picking_type_id.default_location_dest_id.id,
                        'location_dest_id': self.picking_type_id.return_picking_type_id.default_location_dest_id.id or self.picking_type_id.return_picking_type_id.default_location_src_id.id,
                        'group_id': procurement_group.id,  # ระบุ Procurement Group ที่คุณสร้างขึ้น
                        })
        for line in self.claim_modify_line_ids:  # วนลูปสำหรับสินค้าแต่ละรายการ
            qty = line.to_be_replace_quantity or line.quantity
            product_id = line.to_be_replace_product_id or line.product_id
            move = self.env['stock.move'].create({
                'name': line.product_id.name,
                'description_picking': line.description,
                'product_id': product_id.id,
                'product_uom_qty': qty,  # จำนวนสินค้า
                'product_uom': line.product_id.uom_id.id,
                'location_id': self.picking_type_id.return_picking_type_id.default_location_src_id.id or self.picking_type_id.return_picking_type_id.default_location_dest_id.id,
                'location_dest_id': self.picking_type_id.return_picking_type_id.default_location_dest_id.id or self.picking_type_id.return_picking_type_id.default_location_src_id.id,
                'picking_id': new_picking.id,  # ระบุใบ Picking ที่เพิ่งสร้าง
                'origin': self.code,
                'state': 'draft',
            })

        pickings = self.env['stock.picking'].search([('id', '=', new_picking.id)])
        pickings.write({'partner_id': self.return_partner_delivery_id.id})
        self.write({'to_return_picking_ids':[(6, 0, pickings.ids)]})
        pickings[-1].action_assign()

    def prepare_list_based_on_line_operations_modify(self):
        """
        This method is used prepare list of all related operations
        Return: refund_lines, do_lines, so_lines, ro_lines
        """
        refund_lines = []
        do_lines = []
        so_lines = []
        ro_lines = []

        for line in self.claim_modify_line_ids:
            self.check_validate_claim_lines(line)
            if line.claim_type == 'repair':
                ro_lines.append(line)
            if line.claim_type == 'refund':
                refund_lines.append(line)
            if line.claim_type == 'replace_same_product':
                do_lines.append(line)
            if line.claim_type == 'replace_other_product':
                if not line.is_create_invoice:
                    do_lines.append(line)
                else:
                    if line.is_create_invoice:
                        so_lines.append(line)
                        refund_lines.append(line)
                    else:
                        so_lines.append(line)
        return refund_lines, do_lines, so_lines, ro_lines
    
    def action_create_po(self):
        if self.rma_type == 'receive_modify':
            self.check_validate_claim()
            refund_lines, do_lines, so_lines, ro_lines = self.prepare_list_based_on_line_operations_modify()
            if refund_lines:
                self.create_refund(refund_lines)
            if do_lines:
                self.create_do_modify(do_lines)
            if so_lines:
                self.create_so(so_lines)
            if ro_lines:
                self.create_ro_modify(ro_lines)
            self.sudo().action_rma_send_email()
        else: 
            return super(CrmClaimEpt, self).action_create_po()

    def process_claim(self):
        if self.rma_type == 'receive_modify':
            self.check_validate_claim()
            refund_lines, do_lines, so_lines, ro_lines = self.prepare_list_based_on_line_operations_modify()
            if refund_lines:
                self.create_refund(refund_lines)
            if do_lines:
                self.create_do_modify(do_lines)
            if so_lines:
                self.create_so(so_lines)
            if ro_lines:
                self.create_ro_modify(ro_lines)
            self.write({'state':'close'})
            self.sudo().action_rma_send_email()
        else: 
            return super(CrmClaimEpt, self).process_claim()
    
    def create_ro_modify(self, claim_lines):
        """This method is used to create repair order"""
        repair_order_obj = self.env["repair.order"]

        for line in claim_lines:
            repair_order_list = []
            if line.product_id.tracking == 'serial':
                for lot_id in line.serial_lot_ids:
                    repair_order_dict = self.prepare_repair_order_dis_modify(claim_line=line, qty=1)
                    repair_order_dict.update({'lot_id':lot_id.id})
                    repair_order_list.append(repair_order_dict)
            else:
                qty = line.done_qty if line.return_qty == 0.0 else line.return_qty
                repair_order_dict = self.prepare_repair_order_dis_modify(claim_line=line, qty=qty)
                if line.product_id.tracking == 'lot':
                    repair_order_dict.update({'lot_id':line.serial_lot_ids[0].id})
                repair_order_dict['origin_rma'] = self.id
                repair_order_list.append(repair_order_dict)
            repair_order_obj.create(repair_order_list)

    def prepare_repair_order_dis_modify(self, claim_line, qty):
        """Prepare a dictionary for repair orders."""
        location = self.location_id or self.picking_type_id.default_location_dest_id or self.env['stock.warehouse'].search([
            ('company_id', '=', self.company_id.id)], limit=1).lot_stock_id
        repair_type_id = self.env['repair.type'].search([('create_sale_order', '=', True)], limit=1)
        return {
            'repair_type_id':repair_type_id.id,
            'product_id':claim_line.product_id.id,
            'description_rma':claim_line.description,
            'description_rma':claim_line.description,
            'product_qty':qty,
            'claim_id':self.id,
            'partner_id':self.partner_id.id,
            'product_uom':claim_line.product_id.uom_id.id,
            'company_id':self.company_id.id,
            'address_id':self.partner_delivery_id.id,
            'location_id':location.id,
        }

    
    def create_refund_modify(self,refund_lines):
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
            'move_type': 'out_refund',  # กำหนดประเภทเอกสารเป็น Refund
            'invoice_line_ids': invoice_lines,
            'invoice_origin': self.name,
            'claim_id':self.id,
        }

        credit_note = self.env['account.move'].create(credit_note_vals)
        if credit_note:
            self.write({'refund_invoice_ids': [(4, credit_note.id)]})

        return credit_note
    
    def approve_claim(self):
        if self.rma_type == 'receive_modify':
            if len(self.claim_modify_line_ids) <= 0:
                raise UserError(_("Please set return products."))
            
            procurement_group = self.env['procurement.group'].create({
                'name': self.code,
                'move_type': 'direct',  # หรือ 'pull' ตามกรณี
                'picking_id':self.picking_id.id,
                'partner_id':self.partner_delivery_id.id,
            })
            new_picking = self.env['stock.picking'].create({
                        'partner_id': self.partner_id.id,
                        'picking_type_id': self.picking_type_id.id,
                        'state': 'draft',
                        'claim_id':self.id,
                        'origin': self.code,
                        'location_id': self.picking_type_id.default_location_src_id.id,
                        'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                        'group_id': procurement_group.id,  # ระบุ Procurement Group ที่คุณสร้างขึ้น
                        'team_id':self.user_id.sale_team_id.id,
                        })
            
            for line in self.claim_modify_line_ids:  # วนลูปสำหรับสินค้าแต่ละรายการ
                move = self.env['stock.move'].create({
                    'name': line.product_id.name,
                    'description_picking': line.description,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,  # จำนวนสินค้า
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': self.picking_type_id.default_location_src_id.id,
                    'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                    'picking_id': new_picking.id,  # ระบุใบ Picking ที่เพิ่งสร้าง
                    'origin': self.code,
                    'state': 'draft',
                })
                line.move_id = move.id
            self.return_picking_id = new_picking.id
            self.write({'state':'approve'})
            if self.is_not_receipt:

                if self.rma_reason_id.action == 'replace_other_product':
                    self.write({'state':'process'})
                    self.sudo().action_rma_send_email()
                    return
                refund_lines, do_lines, so_lines, ro_lines = self.prepare_list_based_on_line_operations_modify()
                if refund_lines:
                    self.create_refund_modify(refund_lines)
                    # self.create_refund(refund_lines)
                # if do_lines:
                #     self.create_do(do_lines)
                # if so_lines:
                #     self.create_so(so_lines)
                # if ro_lines:
                #     self.create_ro(ro_lines)
                self.write({'state':'process'})
            elif self.is_rma_without_incoming:
                self.write({'state':'process'})
            
            self.sudo().action_rma_send_email()
        else: 
            return super(CrmClaimEpt, self).approve_claim()
        
    def set_claim_modify_line_ids_serial_lot_ids(self):
        for line in self.claim_modify_line_ids:
            move_id = self.return_picking_id.move_lines.filtered( lambda r:r.product_id.id == line.product_id.id and r.description_picking == line.description and r.state == "done")
            if move_id:
                line.serial_lot_ids = move_id.lot_ids.ids
            
    def action_claim_reject_process_ept(self):
        """This method action used to reject claim."""
        return {
            'name':"Reject Claim",
            'view_mode':'form',
            'res_model':'claim.process.wizard',
            'view_id':self.env.ref('rma_ept.view_claim_reject_ept').id,
            'type':'ir.actions.act_window',
            'context':{'claim_lines':self.claim_line_ids.ids,
                       'claim_modify_lines':self.claim_modify_line_ids.ids,
                       'rma_type':self.rma_type,
                       },
            'target':'new'
        }
    def create_do(self, claim_lines):
        if self.picking_id:
            return super(CrmClaimEpt, self).create_do(claim_lines)
        else:
            return self.create_do_no_picking(claim_lines)
            
    def create_do_no_picking(self, claim_lines):
        """based on this method to create a picking one..two or three step."""
        picking_type_id = self.rma_reason_id.operation_type_delivery_id
        if not picking_type_id:
            raise UserError(_("Please set Operation Type for Delivery Location."))
        procurement_group = self.env['procurement.group'].create({
                'name': self.code,
                'move_type': 'direct',
                # 'picking_id':self.picking_id.id,
                'partner_id':self.partner_delivery_id.id,
            })
        new_picking = self.env['stock.picking'].create({
                        'partner_id': self.partner_id.id,
                        'picking_type_id': picking_type_id.id,
                        'state': 'draft',
                        'claim_id':self.id,
                        'origin': self.code,
                        'location_id': picking_type_id.default_location_src_id.id,
                        'location_dest_id': picking_type_id.default_location_dest_id.id or self.partner_delivery_id.property_stock_customer.id,
                        'group_id': procurement_group.id,  # ระบุ Procurement Group ที่คุณสร้างขึ้น
                        })
        for line in claim_lines:
            qty = line.quantity
            product_id = line.product_id
            move = self.env['stock.move'].create({
                'name': line.product_id.name,
                'description_picking': line.description,
                'product_id': product_id.id,
                'product_uom_qty': qty,  # จำนวนสินค้า
                'product_uom': line.product_id.uom_id.id,
                'location_id': picking_type_id.default_location_src_id.id,
                'location_dest_id': picking_type_id.default_location_dest_id.id or self.partner_delivery_id.property_stock_customer.id,
                'picking_id': new_picking.id,  # ระบุใบ Picking ที่เพิ่งสร้าง
                'origin': self.code,
                'state': 'draft',
            })

        pickings = self.env['stock.picking'].search([('id', '=', new_picking.id)])
        pickings.write({'partner_id': self.return_partner_delivery_id.id})
        self.write({'to_return_picking_ids':[(6, 0, pickings.ids)]})
        pickings[-1].action_assign()
