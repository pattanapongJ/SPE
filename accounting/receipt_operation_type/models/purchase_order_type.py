from odoo import models,fields, api,_

class PurchaseOrderTypeInherit(models.Model):
    _inherit = 'purchase.order.type'
    
    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Receipt Operation Type',
        domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id), ('code', '=', 'incoming')]",
        )
    journal_id = fields.Many2one('account.journal', string='Journal', domain="[('type', '=', 'purchase')]")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
         
    @api.onchange('order_type')
    def onchange_order_type(self):
        self.picking_type_id = self.order_type.picking_type_id
        
    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.order_type:
            order_type_journal_id = self.order_type.journal_id
            if order_type_journal_id:
                invoice_vals.update({'journal_id': order_type_journal_id.id})
        return invoice_vals

    
    