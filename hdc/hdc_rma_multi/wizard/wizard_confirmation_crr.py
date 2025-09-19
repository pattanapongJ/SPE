from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round

class CRRForceDoneConfirmationWizard(models.TransientModel):
    _name = 'crr.force.done.confirmation.wizard'
    _description = 'CRR Force Done Confirmation Wizard'

    crr_id = fields.Many2one('customer.return.request', string='CRR')
    message = fields.Text(string='Message')
    has_remaining_items = fields.Boolean(string='Has Remaining Items')
    lang_code = fields.Char(related='crr_id.lang_code', string='Language Code', readonly=True)

    def action_confirm(self):
        self.ensure_one()
        if self.crr_id:
            if self.has_remaining_items:
                remaining_lines = self.crr_id.return_request_lines.filtered(
                    lambda l: l.receive_qty > l.rma_qty
                )

                if remaining_lines:
                    new_picking = self.env['stock.picking'].create({
                            'partner_id': self.crr_id.partner_id.id,
                            'picking_type_id': self.crr_id.picking_type_id.id,
                            'state': 'draft',
                            'origin': self.crr_id.name,
                            'location_dest_id': self.crr_id.picking_type_id.default_location_src_id.id,
                            'location_id': self.crr_id.picking_type_id.default_location_dest_id.id,
                            })
                
                    for line in remaining_lines:
                        remaining_qty = line.receive_qty - line.rma_qty - line.receive_done
                        move = self.env['stock.move'].create({
                            'name': line.product_id.name,
                            'product_id': line.product_id.id,
                            'product_uom_qty': remaining_qty,  # จำนวนสินค้า
                            'product_uom': line.product_id.uom_id.id,
                            'location_dest_id': self.crr_id.picking_type_id.default_location_src_id.id,
                            'location_id': self.crr_id.picking_type_id.default_location_dest_id.id,
                            'picking_id': new_picking.id,  # ระบุใบ Picking ที่เพิ่งสร้าง
                            'origin': self.crr_id.name,
                            'state': 'draft',
                            'company_id': self.crr_id.picking_type_id.company_id.id,
                        })

                    if new_picking:
                        self.crr_id.write({'state': 'done'})
                    else:
                        raise UserError(_("เกิดข้อผิดพลาดในการสร้างใบเบิกสินค้าใหม่") if self.lang_code == 'th_TH' else _("Failed to create new picking document."))
                else:
                    raise UserError(_("ไม่มีสินค้าคงเหลือสำหรับการส่งคืน") if self.lang_code == 'th_TH' else _("There are no remaining items to return."))   
            else:
                raise UserError(_("ไม่มีสินค้าคงเหลือสำหรับการส่งคืน") if self.lang_code == 'th_TH' else _("There are no remaining items to return."))


        return {'type': 'ir.actions.act_window_close'}
    

    def action_discard(self):
        return {'type': 'ir.actions.act_window_close'}


class CRRCancelConfirmationWizard(models.TransientModel):
    _name = 'crr.cancel.confirmation.wizard'
    _description = 'CRR Cancel Confirmation Wizard'

    crr_id = fields.Many2one('customer.return.request', string='CRR')
    message = fields.Text(string='Message')
    lang_code = fields.Char(related='crr_id.lang_code', string='Language Code', readonly=True)

    def action_confirm(self):
        self.ensure_one()
        if self.crr_id:
            self.crr_id.write({'state': 'cancel'})
        pickings = self.env['stock.picking'].search([("origin", "=", self.crr_id.name)])
        if pickings:
            for picking in pickings:
                if picking.state not in ('cancel', 'done'):
                    picking.action_cancel()
                    
        return {'type': 'ir.actions.act_window_close'}

    def action_discard(self):
        return {'type': 'ir.actions.act_window_close'}