from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    deduct_default_product_id = fields.Many2one(
        'product.product',
        'Deduct Deposit Product',
        domain="[('type', '=', 'service')]",
        config_parameter='hdc_deduct_down_payments.default_deduct_product_id',
        help='Default product used for payment advances')