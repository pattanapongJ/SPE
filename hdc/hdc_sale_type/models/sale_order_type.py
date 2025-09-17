from odoo import api, fields, models


class SaleOrderTypology(models.Model):
    _inherit = "sale.order.type"

    team_ids = fields.Many2many(
        comodel_name="crm.team",
        string="Sales Team",
    )
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company.id,readonly=False,)
    warehouse_id = fields.Many2one(comodel_name="stock.warehouse", string="Warehouse",domain="[('company_id', '=', company_id)]")
    branch_id = fields.Many2one('res.branch', string='Branch')

    is_oversea = fields.Boolean(string="Is Oversea", default=False)
    pass_delivery = fields.Boolean(string='Pass Delivery')
    # @api.model
    # def _get_domain_so_sequence_id(self):
    #     seq_type = self.env.ref("sale.seq_sale_order")
    #     return [("code", "=", seq_type.code)]
    
    @api.model
    def _get_domain_sa_sequence_id(self):
        seq_type = "sale.blanket.order"
        return [("code", "=", seq_type)]
    
    @api.model
    def _get_domain_qo_sequence_id(self):
        seq_type = "quotation.order"
        return [("code", "=", seq_type)]

    # so_sequence_id = fields.Many2one(
    #     comodel_name="ir.sequence",
    #     string="Entry Sequence SO",
    #     copy=False,
    #     domain=_get_domain_so_sequence_id,
    # )

    qo_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Entry Sequence QT",
        copy=False,
        domain=_get_domain_qo_sequence_id,
        required=True,
    )

    sa_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Entry Sequence SA",
        copy=False,
        domain=_get_domain_sa_sequence_id,
        required=True,
    )