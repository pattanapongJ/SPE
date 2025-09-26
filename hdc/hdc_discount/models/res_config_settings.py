from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    global_discount_default_product_id = fields.Many2one(
        'product.product',
        'Global Discount Product',
        domain="[('type', '=', 'service')]",
        config_parameter='sale.global_discount_default_product_id',
        help='Default product used for global discount')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("hdc_discount.global_discount_default_product_id", self.global_discount_default_product_id.id)
          

        # self.env['ir.config_parameter'].sudo().set_param("hdc_discount.global_discount_default_product_id", self.global_discount_default_product_id.id)

    # @api.model
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     global_discount = self.env['ir.config_parameter'].sudo().get_param('hdc_discount.global_discount_default_product_id')
    #     # res['global_discount_default_product_id'] = global_discount.id if global_discount else False

    #     print(global_discount , "global_discount 00000000000000000000000000000")
        
    #     return res