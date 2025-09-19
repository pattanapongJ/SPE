from odoo import fields, models, api

class LowStockWizard(models.TransientModel):
    _name = 'low.stock.wizard'
    _description = 'Low Stock Wizard'

    message_low_stock = fields.Char()
    sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')

    # line_ids = fields.One2many('sale.order.line', 'low_stock_wizard_id', string='Line')

    def change_quantity(self):
        alternative_lines = []

        for replace_product in self.sale_order_line_id.product_id.alternative_ids_m2m:
            alternative_lines.append((0, 0, {
                'internal_reference': replace_product.default_code,
                'bns_code': replace_product.bns_code,
                'name': replace_product.name,
                'sales_price': replace_product.lst_price,
                'on_hand': replace_product.qty_available,
                'shipping': replace_product.shipping_qty,
                'incoming_qty': replace_product.incoming_qty,
            }))

        return {
            'name': 'Alternative Product',
            'type': 'ir.actions.act_window',
            'res_model': 'alternative.product.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_internal_reference': self.sale_order_line_id.product_id.default_code,
                'default_bns_code': self.sale_order_line_id.product_id.bns_code,
                'default_name': self.sale_order_line_id.product_id.name,
                'default_sales_price': self.sale_order_line_id.product_id.lst_price,
                'default_on_hand': self.sale_order_line_id.product_id.qty_available,
                'default_incoming_qty': self.sale_order_line_id.product_id.incoming_qty,
                'default_default_replace_product_ids': self.sale_order_line_id.product_id.alternative_ids_m2m.ids,
                'default_alternative_product_ids': alternative_lines,
                'default_sale_order_line_id': self.sale_order_line_id.id,
            },
            # 'context': {'default_message_low_stock': ("You Do Nit Have Stocks For This Product %s" % product.name)},
        } 

    def keep_quantity(self):
        pass