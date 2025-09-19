# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context


class CrmLineEpt(models.Model):
    _inherit = "claim.line.ept"

    #hdc_external_item_customer ไม่ depends ใช้ field นี้ไม่ได้
    external_product_id = fields.Many2one(comodel_name="multi.external.product",string="External Product")
    external_customer = fields.Many2one('res.partner', string="External Customer",store=True)
    external_item = fields.Char(string="External Item",store=True)
    barcode_customer = fields.Char(string="Barcode Customer",store=True)
    barcode_modern_trade = fields.Char(string="Barcode Product",store=True)
    description_customer = fields.Text(string="External Description",store=True)

    @api.onchange('product_id','product_id.product_tmpl_id','claim_id.return_request_id.partner_id')
    def _onchange_external_product(self):
        if self.product_id and self.claim_id.return_request_id:
            if self.product_id.product_tmpl_id and self.claim_id.return_request_id.partner_id:
                external_product = self.env['multi.external.product'].search([
                    ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                    ('partner_id', '=', self.claim_id.return_request_id.partner_id.id),
                    # ('uom_id', '=', self.product_id.uom_id.id)
                ], limit=1)

                if not external_product:
                    external_product = self.env['multi.external.product'].search([
                        ('product_tmpl_id', '=', self.product_template_id.id),
                        ('company_chain_id', '=', self.claim_id.return_request_id.partner_id.company_chain_id.id),
                        # ('uom_id', '=', self.product_id.uom_id.id)
                    ], limit=1)

                self.external_product_id = external_product.id if external_product else False
                if self.external_product_id:
                    # barcode_modern_trade_ids = self.external_product_id.barcode_spe_ids.filtered(lambda x: x.uom_id == self.product_uom)
                    # if barcode_modern_trade_ids:
                    #     barcode_modern_trade = barcode_modern_trade_ids[0].barcode_modern_trade
                    # else:
                    #     barcode_modern_trade = False
                    self.external_item = self.external_product_id.name
                    self.barcode_customer = self.external_product_id.barcode_modern_trade
                    self.barcode_modern_trade = self.external_product_id.barcode_modern_trade
                    self.description_customer = self.external_product_id.product_description
                else:
                    self.external_item = False
                    self.barcode_customer = False
                    self.barcode_modern_trade = False
                    self.description_customer = False
        else:
            self.external_item = False
            self.barcode_customer = False
            self.barcode_modern_trade = False
            self.description_customer = False
        

class CrmClaimEpt(models.Model):
    _inherit = "crm.claim.ept"

    return_request_id = fields.Many2one(comodel_name="customer.return.request",copy=False)

    def unlink(self):
        for rec in self:
            if rec.return_request_id and rec.claim_line_ids:
                if rec.return_request_id.return_request_lines:
                    for rma_line_id in rec.claim_line_ids:
                        for request_line in rec.return_request_id.return_request_lines:
                            if rma_line_id.product_id.id == request_line.product_id.id:
                                new_rma_qty = request_line.rma_qty - rma_line_id.quantity
                                data = {"rma_qty":  new_rma_qty}
                                if new_rma_qty == 0:
                                    data["state"] = "draft"
                                request_line.write(data)
        res = super(CrmClaimEpt,self).unlink()
        return res
    
    def create_refund(self, claim_lines):
        if self.return_request_id:
            return self.create_refund_crr(claim_lines)
        else:
            return super(CrmClaimEpt, self).create_refund(claim_lines)

    def create_refund_crr(self, claim_lines):
        """This method used to create a refund."""
        if not self.sale_id.invoice_ids:
            message = _(
                "The invoice was not created for Order : "
                "<a href=# data-oe-model=sale.order data-oe-id=%d>%s</a>") % (
                    self.sale_id.id, self.sale_id.name)
            self.message_post(body=message)
            return False
        refund_invoice_ids_rec = []

        refund_invoice_ids = self.check_and_create_refund_crr_invoice(claim_lines)
        if not refund_invoice_ids:
            return False
        refund_invoice_ids_rec = self.prepare_and_create_refund_crr_invoice \
            (refund_invoice_ids, refund_invoice_ids_rec)

        if refund_invoice_ids_rec:
            self.write({'refund_invoice_ids':[(6, 0, refund_invoice_ids_rec)]})
        return True

    def prepare_and_create_refund_crr_invoice(self, refund_invoice_ids, refund_invoice_ids_rec):
        """prepare values for refund invoice and create refund invoice."""
        for invoice_id, lines in refund_invoice_ids.items():
            refund_invoice = self.create_reverse_move_for_invoice(invoice_id)
            if not refund_invoice:
                continue

            if refund_invoice and refund_invoice.invoice_line_ids:
                refund_invoice.invoice_line_ids.with_context(check_move_validity=False).unlink()

            for line in lines:
                if not list(line.keys()) or not list(line.values()):
                    continue

                product_id = self.env['product.product'].browse(list(line.keys())[0])
                if not product_id:
                    continue
                move_line_vals = self.prepare_move_line_vals(product_id, refund_invoice, line)
                line_vals = self.env['account.move.line'].new(move_line_vals)

                line_vals._onchange_product_id()
                line_vals = line_vals._convert_to_write(
                    {name:line_vals[name] for name in line_vals._cache})
                line_vals.update({
                    'sale_line_ids':[(6, 0, [line.get('sale_line_id')] or [])],
                    'tax_ids':[(6, 0, line.get('tax_id') or [])],
                    'quantity':list(line.values())[0],
                    'price_unit': line.get('price'),
                })
                self.env['account.move.line'].with_context(check_move_validity=False).create(
                    line_vals)

            refund_invoice.with_context(check_move_validity=False)._recompute_dynamic_lines(
                recompute_all_taxes=True)
            refund_invoice_ids_rec.append(refund_invoice.id)
        return refund_invoice_ids_rec

    def check_and_create_refund_crr_invoice(self, claim_lines):
        """
        This method is used to check invoice is posted or not and
        according to invoice it'll create refund invoice

        """
        product_process_dict = {}
        refund_invoice_ids = {}

        for line in claim_lines:
            if self.is_rma_without_incoming and line.id not in product_process_dict:
                qty = line.quantity if line.to_be_replace_quantity <= 0 else \
                    line.to_be_replace_quantity
                product_process_dict.update({line.id:{'total_qty':qty, 'invoice_line_ids':{}}})

            if line.id not in product_process_dict and self.is_not_receipt:
                product_process_dict.update({line.id:{'total_qty':line.quantity, 'invoice_line_ids':{}}})

            if line.id not in product_process_dict:
                product_process_dict.update({line.id:{'total_qty':line.return_qty,
                                                      'invoice_line_ids':{}}})

            invoice_lines = self.account_id.invoice_line_ids
            for invoice_line in invoice_lines.filtered(
                    lambda l: l.move_id.move_type == 'out_invoice'):
                if invoice_line.move_id.state != 'posted':
                    message = _("The invoice was not posted. Please check invoice :"
                                "<a href=# data-oe-model=account.move data-oe-id=%d>%s</a>") % (
                                    invoice_line.move_id.id, invoice_line.move_id.display_name)
                    self.message_post(body=message)
                    return False

                product_line = product_process_dict.get(line.id)
                if product_line.get('process_qty', 0) < product_line.get('total_qty', 0):
                    product_line, process_qty = self.prepare_product_qty_dict \
                        (product_line, invoice_line)

                    product_line.get('invoice_line_ids').update({
                        invoice_line.id:process_qty,
                        'invoice_id':invoice_line.move_id.id
                    })

                    refund_invoice_ids = self.prepare_refund_crr_invoice_dict(
                        invoice_line, refund_invoice_ids, invoice_line, process_qty)

        return refund_invoice_ids
    
    def prepare_refund_crr_invoice_dict(self, line, refund_invoice_ids, invoice_line, process_qty):
        """prepare refund invoice values based on invoice"""
        sale_line = invoice_line.sale_line_ids
        refund_invoice_vals = self.add_dict_values_for_refund_invoice \
            (sale_line, invoice_line, process_qty)

        if refund_invoice_ids.get(invoice_line.move_id.id):
            refund_invoice_ids.get(invoice_line.move_id.id).append(refund_invoice_vals)
        else:
            refund_invoice_ids.update({invoice_line.move_id.id:[refund_invoice_vals]})

        return refund_invoice_ids

    @staticmethod
    def add_dict_values_for_refund_invoice(sale_line, invoice_line, process_qty):
        """add dictionary values on refund invoice"""
        return {
            invoice_line.product_id.id:process_qty,
            'price': sale_line.price_unit,
            'tax_id':sale_line.tax_id.ids,
            'discount':sale_line.discount,
            'triple_discount':sale_line.triple_discount,
            'sale_line_id':sale_line.id,
        }
    # ปิดเรื่องที่ไปdoneใบ CRR ถ้าปิดใบ rma ครบ ไปก่อน
    # def process_claim(self):
    #     res = super().process_claim()
    #     if self.return_request_id and self.state == "close":
    #         claim_ids = self.env['crm.claim.ept'].search([('return_request_id','=',self.return_request_id.id)])
    #         if claim_ids:
    #             check_status_close = True
    #             for claim in claim_ids:
    #                 if claim.state != "close":
    #                     check_status_close = False
    #             if check_status_close:
    #                 self.return_request_id.write({
    #                     "state": "done"
    #                 })

    #     return res
 



