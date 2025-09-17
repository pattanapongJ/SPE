# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context

class CRMClaimLine(models.Model):
    _inherit = 'claim.line.ept'
    _description = 'CRM Claim Line'

    # @api.constrains('quantity')
    # def check_qty(self):
    #     if self.claim_id.is_select_product_receipt:
    #         return
    #     else :
    #         return super(CRMClaimLine, self).check_qty()
        
    def _prepare_invoice_line(self):
        self.ensure_one()
        res = {
            'name': self.product_id.display_name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_id.uom_id.id,
            'quantity': self.quantity,
            'price_unit': self.product_id.lst_price,
            'analytic_account_id':  False,
        }
        return res
    
    def _compute_return_quantity(self):
        """
        This method used to set a return quantity in the claim line base on the return move.
        """
        for record in self:
            record.return_qty = 0
            if record.claim_id.return_picking_id:
                move_line = record.claim_id.return_picking_id.mapped('move_lines') \
                    .filtered(lambda r: r.product_id.id == record.product_id.id)
                record.return_qty = move_line.quantity_done