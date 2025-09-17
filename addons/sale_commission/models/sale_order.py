# Copyright 2014-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("order_line.agent_ids.amount")
    def _compute_commission_total(self):
        for record in self:
            record.commission_total = sum(record.mapped("order_line.agent_ids.amount"))

    commission_total = fields.Float(
        string="Commissions",
        compute="_compute_commission_total",
        store=True,
    )

    partner_agent_ids = fields.Many2many(
        string="Agents",
        comodel_name="res.partner",
        compute="_compute_agents",
        search="_search_agents",
    )

    internal_agents = fields.Many2one(string = "Internal Agents", comodel_name = "res.partner",
                                      domain = "[('agent', '=', True),('agent_type', '=', 'internal_agent')]")
    external_agents = fields.Many2one(string = "External Agents", comodel_name = "res.partner", domain="[('agent', '=', True),('agent_type', '=', 'agent')]")
    driver_agents = fields.Many2one(string = "Driver", comodel_name = "res.partner", domain="[('agent', '=', True),('agent_type', '=', 'driver')]")

    # @api.onchange('internal_agents','external_agents', 'driver_agents')
    def _commission_agent(self):
        customer = []
        for rec in self:
            for line in rec.order_line:
                line.agent_ids.unlink()
                if rec.external_agents:
                    agent_ids = self.env["sale.order.line.agent"].create({
                        "object_id": line._origin.id,
                        "agent_id": rec.external_agents.id,
                        "commission_id": rec.external_agents.commission_id.id
                        })
                    # line.agent_ids = agent_ids
                if rec.internal_agents:
                    agent_ids = self.env["sale.order.line.agent"].create({
                        "object_id": line._origin.id, "agent_id": rec.internal_agents.id,
                        "commission_id": rec.internal_agents.commission_id.id
                        })
                    # line.agent_ids = agent_ids
                if rec.driver_agents:
                    agent_ids = self.env["sale.order.line.agent"].create({
                        "object_id": line._origin.id, "agent_id": rec.driver_agents.id,
                        "commission_id": rec.driver_agents.commission_id.id
                        })
                    # line.agent_ids = agent_ids

    @api.depends("partner_agent_ids", "order_line.agent_ids.agent_id")
    def _compute_agents(self):
        for so in self:
            so.partner_agent_ids = [
                (6, 0, so.mapped("order_line.agent_ids.agent_id").ids)
            ]

    @api.model
    def _search_agents(self, operator, value):
        sol_agents = self.env["sale.order.line.agent"].search(
            [("agent_id", operator, value)]
        )
        return [("id", "in", sol_agents.mapped("object_id.order_id").ids)]

    def recompute_lines_agents(self):
        self.mapped("order_line").recompute_agents()


class SaleOrderLine(models.Model):
    _inherit = [
        "sale.order.line",
        "sale.commission.mixin",
    ]
    _name = "sale.order.line"

    agent_ids = fields.One2many(comodel_name="sale.order.line.agent")

    @api.model
    def create(self, values):
        val = super().create(values)
        rec = val.order_id
        val.agent_ids = False
        if rec.external_agents:
            agent_ids = self.env["sale.order.line.agent"].create({
                "object_id": val.id, "agent_id": rec.external_agents.id,
                "commission_id": rec.external_agents.commission_id.id
                })
        if rec.internal_agents:
            agent_ids = self.env["sale.order.line.agent"].create({
                "object_id": val.id, "agent_id": rec.internal_agents.id,
                "commission_id": rec.internal_agents.commission_id.id
                })
        if rec.driver_agents:
            agent_ids = self.env["sale.order.line.agent"].create({
                "object_id": val.id, "agent_id": rec.driver_agents.id,
                "commission_id": rec.driver_agents.commission_id.id
                })
        return val


    @api.depends("order_id.partner_id")
    def _compute_agent_ids(self):
        self.agent_ids = False  # for resetting previous agents
        for record in self.filtered(lambda x: x.order_id.partner_id):
            if not record.commission_free:
                record.agent_ids = record._prepare_agents_vals_partner(
                    record.order_id.partner_id
                )

    def _prepare_invoice_line(self, **optional_values):
        vals = super()._prepare_invoice_line(**optional_values)
        vals["agent_ids"] = [
            (0, 0, {"agent_id": x.agent_id.id, "commission_id": x.commission_id.id})
            for x in self.agent_ids
        ]
        return vals


class SaleOrderLineAgent(models.Model):
    _inherit = "sale.commission.line.mixin"
    _name = "sale.order.line.agent"
    _description = "Agent detail of commission line in order lines"

    object_id = fields.Many2one(comodel_name="sale.order.line")
    currency_id = fields.Many2one(related="object_id.currency_id")

    @api.depends(
        "commission_id",
        "object_id.price_subtotal",
        "object_id.product_id",
        "object_id.product_uom_qty",
    )
    def _compute_amount(self):
        for line in self:
            order_line = line.object_id
            line.amount = line._get_commission_amount(
                line.commission_id,
                order_line.price_subtotal,
                order_line.product_id,
                order_line.product_uom_qty,
            )
