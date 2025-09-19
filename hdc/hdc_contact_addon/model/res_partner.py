# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_factory = fields.Boolean(string="Factory")
    is_trading = fields.Boolean(string="Trading")
    carrier_id = fields.Many2one("delivery.carrier", string="Delivery Mode")
    employee_id = fields.Many2one("hr.employee", string="Employee")
    line_id = fields.Char(string="Line ID")
    # purchase_team = fields.Many2one("purchase.team", string="Purchase Team")
    # shipping = fields.Char(string="Shipping")

    property_product_pricelist = fields.Many2one(
        'product.pricelist', 
        'Pricelist', 
        company_dependent=True,
        domain=lambda self: [('company_id', 'in', (self.env.company.id, False))],
        help="This pricelist will be used, instead of the default one, for sales to the current partner"
    )

    def _commercial_fields(self):
        return super(ResPartner, self)._commercial_fields() + ['property_product_pricelist']