from odoo import api, fields, models, _

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    product_type_id = fields.Many2one('product.type.mr',string='Product Type')
