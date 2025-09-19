# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'
    _description = 'Return Picking'

    remark = fields.Text(string="Remark", required=True)


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _order = 'create_date desc'

    purchase_claim_count_out = fields.Integer(compute='_compute_purchase_claim_count_out', string="Claim Count")
    purchase_claim_id = fields.Many2one('purchase.crm.claim.ept', string="RMA Claim", copy=False)
    rma_purchase_id = fields.Many2one('purchase.order', string="Rma Purchase Order", copy=False)
    repair_order_id = fields.Many2one('repair.order', string="Repair Order", copy=False)
    view_purchase_claim_button = fields.Boolean(compute='_compute_view_purchase_claim_button')

    def _compute_purchase_claim_count_out(self):
        """
        This method used to display the number of a claim for related picking.
        """
        for record in self:
            record.purchase_claim_count_out = self.env['purchase.crm.claim.ept'].search_count \
                ([('picking_id', '=', record.id)])

    def _compute_view_purchase_claim_button(self):
        """
        This method used to display a claim button on the picking based on the picking stage.
        """
        for record in self:
            record.view_purchase_claim_button = False
            if record.purchase_id and record.state == 'done' and \
                    record.picking_type_code in ( \
                    'outgoing', 'internal'):
                record.view_purchase_claim_button = True

    def write(self, vals):
        """
        This methos is used to write state of related claim.
        """
        for record in self.filtered(lambda l: l.state == 'done' and \
                                    l.picking_type_code == 'outgoing' and l.purchase_claim_id and \
                                    l.purchase_claim_id.state == 'approve'):
            record.purchase_claim_id.write({'state':'process'})
        return super().write(vals)
