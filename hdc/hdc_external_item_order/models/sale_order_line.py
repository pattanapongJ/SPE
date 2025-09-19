from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # external_customer = fields.Many2one('res.partner', string="External Customer")
    # barcode_customer = fields.Char(related="external_product_id.barcode_modern_trade")
    # description_customer = fields.Text(related="external_product_id.product_description", string="External Description")
    # barcode_modern_trade = fields.Char(string="Barcode Product", compute="compute_barcode_modern_trade", store=False)


    # @api.depends("external_product_id")
    # def compute_barcode_modern_trade(self):
    #     for obj in self:
    #         barcode_modern_trade = ' '.join(obj.external_product_id.barcode_spe_ids.filtered(lambda a: a.uom_id.id == obj.product_uom.id).mapped('barcode_modern_trade'))
    #         obj.barcode_modern_trade = barcode_modern_trade or ''
