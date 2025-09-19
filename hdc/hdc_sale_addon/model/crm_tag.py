from odoo import fields, models


class TagInherit(models.Model):
    _inherit = "crm.tag"

    default_product_tag = fields.Boolean(
        string="Default Product Tag",
        help="Check this box if you want to set this tag as the default tag for products."
    )

