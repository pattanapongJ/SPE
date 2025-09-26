from datetime import date

from odoo import api, fields, models, _


class CrmTeam(models.Model):
    _inherit = "crm.team"

    sale_type_ids = fields.Many2many(comodel_name="sale.order.type", string="Sale Type")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    type_id = fields.Many2one(
        comodel_name="sale.order.type",
        string="Sale Type",
        compute="_compute_sale_type_id",
        store=True,
        readonly=True,
        states={
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
        },
        # default=lambda so: so._default_type_id(),
        # domain="[('id', 'in', sale_type_ids)]",
        ondelete="restrict",
        copy=True,
    )

    is_oversea = fields.Boolean(related='type_id.is_oversea')
    
    sale_type_ids = fields.Many2many(related="team_id.sale_type_ids")

    is_below_cost = fields.Boolean(string="Is below cost", default=False)

    is_confirm_below_cost = fields.Boolean(
        string="Approve Below Cost", default=False, copy=False, tracking = 2
    )
    user_approve_below_cost = fields.Many2one('hr.employee', string = 'Approve Below Employee', tracking = 2)
    
    # @api.onchange("team_id")
    # def _domain_type_id(self):
    #     if self.team_id:
    #         return {
    #             "domain": {"type_id": [("id", "in", self.team_id.sale_type_ids.ids)]}
    #         }
    #     else:
    #         return {"domain": {"type_id": []}}
    
    @api.onchange('type_id')
    def _onchange_sale_type(self):
        for order in self:
            # if order.type_id and order.type_id.pricelist_id:
            #     order.pricelist_id = order.type_id.pricelist_id
            if order.type_id.branch_id:
                order.branch_id = order.type_id.branch_id

    def action_draft(self):
        self.is_confirm_below_cost = False
        return super(SaleOrder, self).action_draft()