# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree
from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
from odoo.tools.misc import format_date
from collections import defaultdict
import re

class BlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    invoice_count = fields.Integer(compute="_compute_invoice", string='Invoice Count', copy=False, default=0, store=True)
    invoice_ids = fields.Many2many('account.move', compute="_compute_invoice", string='Bills', copy=False, store=True)
    
    @api.depends('line_ids')
    def _compute_invoice(self):
        for order in self:
            invoices = order.env["account.move"].search([("sale_agreement_id", "=", order.id)])
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)

    def copy_data(self, default=None):
        if default is None:
            default = {}
        default["line_ids"] = [
            (0, 0, line.copy_data()[0])
            for line in self.line_ids.filtered(lambda l: not l.is_deposit)
        ]
        return super(BlanketOrder, self).copy_data(default)
    
    def action_view_invoice(self, invoices=False):
        """This function returns an action that display existing vendor bills of
        given purchase order ids. When only one found, show the vendor bill
        immediately.
        """
        if not invoices:
            # Invoice_ids may be filtered depending on the user. To ensure we get all
            # invoices related to the purchase order, we read them in sudo to fill the
            # cache.
            self.sudo()._read(['invoice_ids'])
            invoices = self.invoice_ids

        result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        # choose the view_mode accordingly
        if len(invoices) > 1:
            result['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = invoices.id
        else:
            result = {'type': 'ir.actions.act_window_close'}

        return result
    
    def action_advance_payment_inv(self):
        self.ensure_one()
        product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
        product = self.env["product.product"].browse(int(product_id))
        return {
                "name": "Invoice Order",
                "type": "ir.actions.act_window",
                "res_model": "sale.agreement.advance.payment.inv",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_sale_agreement_deposit_product_id": product.id,
                            },

            }
    
    @api.depends(
        "line_ids.remaining_uom_qty",
        "validity_date",
        "confirmed",
    )
    def _compute_state(self):
        today = fields.Date.today()
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        for order in self:
            if not order.confirmed:
                order.state = "draft"
            elif order.validity_date and order.validity_date <= today and order.state != "cancel":
                order.state = "expired"
            else:
                # Filter line_ids to exclude is_deposit = True
                filtered_lines = order.line_ids.filtered(lambda line: not line.is_deposit)
                remaining_qty_sum = sum(filtered_lines.mapped("remaining_uom_qty"))
                # if float_is_zero(remaining_qty_sum, precision_digits=precision):
                if all(qty <= 0 for qty in filtered_lines.mapped("remaining_uom_qty")):
                    order.state = "done"
                else:
                    order.state = "open"

    
class BlanketOrderLine(models.Model):
    _inherit = "sale.blanket.order.line"
    
    is_deposit = fields.Boolean(
        string="Is a down payment", copy=False
    )
    deposit_history_ids = fields.One2many(
        'sale.blanket.deposit.order.history', 
        'sale_agreement_line_id',
        string='Deposit History',
    )

class SaleBlanketOrderDepositHistory(models.Model):
    _name = 'sale.blanket.deposit.order.history'
    _description = 'History of Deposits Deducted from Sales Blanket Order Lines'

    sale_agreement_line_id = fields.Many2one('sale.blanket.order.line', string='Sale Blanket Order Line', required=True, ondelete='cascade')
    deposit_move_id = fields.Many2one('account.move', string='Deposit Invoice', required=True, ondelete='cascade')
    deduct_move_id = fields.Many2one('account.move', string='Deduct Invoice', required=True, ondelete='cascade')
    deducted_amount = fields.Monetary(string='Deducted Amount', required=True)
    currency_id = fields.Many2one(related='sale_agreement_line_id.currency_id', store=True)
    deduct_state = fields.Selection(related='deduct_move_id.state')

