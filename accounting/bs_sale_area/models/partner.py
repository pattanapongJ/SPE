from odoo import api, models, fields

class PartnerAddAreaSaleCode(models.Model):
    _inherit = 'res.partner'
    area_sale_code = fields.Char(string="Area Sale Code")
