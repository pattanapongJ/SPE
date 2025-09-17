# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import time

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


class CrmClaimEpt(models.Model):
    _inherit = "purchase.crm.claim.ept"
    _description = 'RMA CRM Claim Purchase'

    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        if self.invoice_id and not self.purchase_id:
            purchase_id = self.env["purchase.order"].search([('invoice_ids', '=', self.invoice_id.id)])
            values = {'purchase_id': purchase_id,}
            self.update(values)

    @api.onchange('purchase_id')
    def onchange_purchase_id(self):
        if self.purchase_id:
            invoice_ids = self.purchase_id.invoice_ids
            invoice_id_can_be_use = []
            self.invoice_id = False
            for line_invoice_ids in invoice_ids:
                if line_invoice_ids.state == 'posted':
                    invoice_id_can_be_use.append(line_invoice_ids.id)
            line_invoice_id = len(invoice_id_can_be_use)
            if line_invoice_id > 0:
                self.invoice_id = invoice_id_can_be_use[0]
            picking = False
            for line_picking in self.purchase_id.picking_ids:
                if line_picking.state == 'done' and line_picking.picking_type_code == 'incoming':
                    picking = line_picking
            if picking:
                self.picking_id = picking.id
            if self.picking_id:
                self.change_field_based_on_picking()
            picking_can_be_use = self._data_picking()
            return {"domain": {"picking_id": [('id', 'in', picking_can_be_use), ('picking_type_code', '=', 'incoming'), ('purchase_id', '=', self.purchase_id.id)],
                                "invoice_id":[('id','in',invoice_id_can_be_use)]}}
        else:
            self.partner_id = False
            self.partner_phone = False
            self.email_from = False
            self.partner_delivery_id = False
            picking_can_be_use = self._data_picking()
            return {"domain": {"picking_id": [('id', 'in', picking_can_be_use), ('picking_type_code', '=', 'incoming'), ('purchase_id', '!=', False)]}}
