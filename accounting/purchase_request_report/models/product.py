from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    remark = fields.Text(string='Remark')