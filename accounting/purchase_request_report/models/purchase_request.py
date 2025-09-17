from odoo import fields, models, api


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    remark = fields.Text(string='Remark')
    for_customer = fields.Many2one('res.partner', string='For Customer')

class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    remark = fields.Text(string='Remark')

    @api.onchange("product_id")
    def onchange_product_remark(self):
        if self.product_id:
            remark = self.product_id.remark
            self.remark = remark or False
            