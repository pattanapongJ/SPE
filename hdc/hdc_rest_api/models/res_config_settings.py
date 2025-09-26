from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_discount_id = fields.Many2one(
        'product.product',
        'Discount Product',
        domain="[('type', '=', 'service')]",
        config_parameter='hdc_rest_api.product_discount_id',
        help='Default product used for discount')

    product_delivery_id = fields.Many2one(
        'product.product',
        'Delivery Fee',
        domain="[('type', '=', 'service')]",
        config_parameter='hdc_rest_api.product_delivery_id',
        help='Default product used for Delivery fee')
    
