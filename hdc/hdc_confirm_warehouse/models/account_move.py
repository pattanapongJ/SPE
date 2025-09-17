from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    stock_batch_id = fields.Many2one('stock.picking.batch', string="Stock Picking Batch")

    def action_post(self):
        res = super().action_post()
        for rec in self:
            if rec.stock_batch_id:
                rec.stock_batch_id.bill_status = 'biled'
        return res