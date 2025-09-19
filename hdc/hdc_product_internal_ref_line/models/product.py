# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def name_get(self):
        result = super().name_get()
        cleaned_result = []
        for record_id, name in result:
            if name.startswith('['):
                closing = name.find(']')
                if closing != -1:
                    name = name[closing + 2:]
            cleaned_result.append((record_id, name))
        return cleaned_result
