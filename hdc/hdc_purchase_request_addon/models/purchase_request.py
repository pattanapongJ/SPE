from odoo import _, api, fields, models
from odoo.exceptions import UserError

class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    team_id = fields.Many2one(
        comodel_name="purchase.team",
        string="Purchase Team",
        domain=lambda self: self._get_domain_team_id()
    )

    def _get_domain_team_id(self):
        user_company = self.env.company
        teams = self.env["purchase.team"].search([('company_id', '=', user_company.id)])
        if teams:
            return [('id', 'in', teams.ids)]
        else:
            return []

    partner_pr = fields.Char(string="Partner")

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        user_company = self.env.user.company_id
        teams = self.env['purchase.team'].search([('company_id', '=', user_company.id)])
        if not teams:
            teams = self.env['purchase.team'].search([])
        res['team_id'] = teams and teams[0].id or False
        return res

class PurchaseRequestLine(models.Model):
    _inherit = "purchase.request.line"

    # unit_price = fields.Monetary('Unit Price',currency_field="currency_id",default=0.0,)
    unit_price = fields.Float(
        'Unit Price',
        related='product_id.last_purchase_price',
        digits='Product Price', # Recommended for currency-related floats
    )
    mix = fields.Float(string="Mix", related="orderpoint_id.product_min_qty", store=True)
    max = fields.Float(string="Max", related="orderpoint_id.product_max_qty", store=True)
    box_qty = fields.Integer(string="กล่องละ", related="product_id.product_tmpl_id.box")
    crate_qty = fields.Integer(string="ลังละ", related="product_id.product_tmpl_id.crate")

    orderpoint_id = fields.Many2one(
        'stock.warehouse.orderpoint',
        compute='_compute_orderpoint_id',
        store=True,
        string="Reordering Rule ID"
    )

    @api.depends('product_id')
    def _compute_orderpoint_id(self):
        for rec in self:
            rec.orderpoint_id = self.env['stock.warehouse.orderpoint'].search([
                ('product_id', '=', rec.product_id.id)
            ], limit=1)
