from odoo import _, fields, models
class SaleOrderConfirmAddlineWizard(models.TransientModel):
    _name = 'sale.order.confirm.addline.wizard'
    _description = 'Confirmation Wizard for Add Line'

    message = fields.Text(string="Message", readonly=True)
    order_id = fields.Many2one('sale.order', string="Order", readonly=True)

    def action_confirm_addline(self):

        result = self.order_id.action_sale_ok2()
        # if result.get('res_model') == 'customer.limit.wizard':
        #     result['target'] = 'current'
        return result
        # print('result---------------------->', result)
        # return result
