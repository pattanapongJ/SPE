from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class ConfirmDeliveryNote(models.TransientModel):
    _name = "wizard.confirm.delivery.noted"
    _description = "Wizard Confirm Delivery Noted"

    transport_line_id = fields.Many2one('delivery.round',string="สายส่ง TRL", copy=False)
    company_round_id = fields.Many2one('company.delivery.round', string="Mode of delivery", copy=False)
    scheduled_date = fields.Date(string="Scheduled Date", default=lambda self: fields.Date.today())
    delivery_by_id = fields.Many2one('res.users', string="Delivery By", default=lambda self: self.env.user)
    search_id = fields.Many2one("resupply.transfer.branch.summary")
    company_id = fields.Many2one("res.company", string="Company")

    def confirm_delivery_action(self):
        order_line = []
        distribition_note = self.env['distribition.delivery.note']
        distribition_note_id = distribition_note.create({
            'name': 'New',
            # 'schedule_date': self.scheduled_date,
            'company_round_id': self.company_round_id.id,
            'transport_line_id': self.transport_line_id.id,
            'company_id': self.company_id.id,
        })
       
        for invoice_line in self.search_id.invoice_line_ids.filtered(lambda x: x.selected):
            invoice_cancel_state = 'cancel' if invoice_line.invoice_id.state == 'cancel' else 'none'
            line = (0, 0, {
                'distribition_id': distribition_note_id.id,
                'invoice_id': invoice_line.invoice_id.id,
                'partner_id': invoice_line.partner_id.id,
                'delivery_address_id': invoice_line.delivery_address_id.id,
                'transport_line_id': invoice_line.transport_line_id.id,
                'company_round_id': invoice_line.company_round_id.id,
                'sale_no': invoice_line.sale_no,
                'delivery_id': invoice_line.delivery_id.id,
                'sale_person': invoice_line.sale_person.id,
                'invoice_status': invoice_line.status,
                'invoice_date': invoice_line.invoice_id.invoice_date,
                'billing_status': 'none',
                'invoice_cancel_state': invoice_cancel_state
            })

            order_line.append(line)
        if order_line:
            distribition_note_id.write({
                'invoice_line_ids': order_line
            })
        else:
            raise UserError(_("Please select at least one invoice line"))

        action = {
            'name': "Generate Distribution Delivery Note",
            'view_mode': 'form',
            'res_model': 'distribition.delivery.note',
            'type': 'ir.actions.act_window',
            'res_id': distribition_note_id.id,
        }
        return action
        