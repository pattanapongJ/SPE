from collections import defaultdict

from odoo import _, fields, models
class SaleOrderConfirmAddlineWizard(models.TransientModel):
    _name = 'sale.order.confirm.addline.wizard'
    _description = 'Confirmation Wizard for Add Line'

    message = fields.Text(string="Message", readonly=True)
    order_id = fields.Many2one('sale.order', string="Order", readonly=True)

    def action_sale_ok2(self):
        result = self.order_id.with_context(order_id=self.order_id.id).action_sale_ok2()
        return result