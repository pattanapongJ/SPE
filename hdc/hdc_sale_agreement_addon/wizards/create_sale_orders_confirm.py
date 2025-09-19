# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from collections import defaultdict

from odoo import _, fields, models

class SaleBlanketOrderConfirmationWizard(models.TransientModel):
    _name = 'sale.blanket.order.confirmation.wizard'
    _description = 'Confirmation Wizard for Expired Sale Agreement'

    message = fields.Text(string="Message", readonly=True)
    blanket_order_id = fields.Many2one('sale.blanket.order', string="Blanket Order", readonly=True)

    def action_create_sale_order(self):
        """
        Open the Create Sale Order wizard.
        """
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Sale Order'),
            'res_model': 'sale.blanket.order.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_blanket_order_id': self.blanket_order_id.id,  # ส่ง Blanket Order ที่ถูกต้อง
            },
        }


    def action_close(self):
        """
        Close the wizard without creating a Sale Order
        """
        return {'type': 'ir.actions.act_window_close'}
