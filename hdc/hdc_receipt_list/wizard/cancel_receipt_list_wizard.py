# -*- coding: utf-8 -*-
from odoo import _, api, fields, models

class CancelReceiptListWizard(models.TransientModel):
    _name = 'cancel.receipt.list.wizard'
    _description = 'Cancel Receipt List Wizard'

    reason = fields.Text(string='Reason', required=True)
    receipt_list_id = fields.Many2one('receipt.list', string='Receipt List')

    def confirm_cancel(self):
        receipt_list = self.receipt_list_id
        for line in receipt_list.line_ids:
            if line.move_id.origin_rl_move_id:
                if line.move_id.origin_rl_move_id.receipt_list_line_id:
                    line.move_id.receipt_list_line_id = False
                else:
                    line.move_id.origin_rl_move_id.product_uom_qty += line.move_id.product_uom_qty
                    line.move_id.picking_id = False
                    line.move_id._action_cancel()
            else:
                for move in line.move_id.rl_move_ids:
                    if move.state not in ('done', 'cancel', 'skip_done') and not move.receipt_list_line_id:
                        line.move_id.product_uom_qty += move.product_uom_qty
                        move.picking_id = False
                        move._action_cancel()
                line.move_id.receipt_list_line_id = False

        # for line in receipt_list.line_service_ids:
        #     line.purchase_line_id.service_list_id = False

        receipt_list.write(
                    {
                        'invoice_no': '',
                        'performa_invoice': '',
                        'commercial_invoice': '',
                        'state': 'cancel',
                        'warehouse_status': 'cancel',
                        'inventory_status': 'cancel',
                    }
                )

        receipt_list.message_post(body=f"Receipt List cancelled. Reason: {self.reason}")
        return {'type': 'ir.actions.act_window_close'}