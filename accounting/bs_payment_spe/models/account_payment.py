# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    book_no = fields.Char(string="Book No.")
    no = fields.Char(string="No.")
    messenger_name = fields.Many2one(string="Message Name",comodel_name='hr.employee')
    commission_date = fields.Date(string="Commission Date")
    internal_note = fields.Char(string="Internal Note")
    saleperson_id = fields.Many2one("res.users", string="Saleperson")
    document_ref = fields.Char(string="Document Ref.")
    pdc_ref = fields.Char(string="PDC Reference", compute="_compute_pdc_ref")

    @api.depends("pdc_id")
    def _compute_pdc_ref(self):
        for rec in self:
            rec.pdc_ref = rec.pdc_id.name or ""


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    book_no = fields.Char(string="Book No.")
    no = fields.Char(string="No.")
    messenger_name = fields.Many2one(string="Message Name",comodel_name='hr.employee')

    def _create_payment_vals_from_wizard(self):
        val = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        if self.partner_type == "customer":
            val["saleperson_id"] = self._get_saleperson()
        val.update(
            {
                "book_no": self.book_no,
                "no": self.no,
                "messenger_name": self.messenger_name.id if self.messenger_name else False,
                "branch_id": self.branch_id.id
            }
        )
        return val

    def _get_saleperson(self):
        move_ids = self.line_ids.mapped("move_id")
        if not move_ids:
            return None
        for move in move_ids.sorted(key=lambda m: m.invoice_date):
            return move.invoice_user_id.id

    def _create_payment_vals_from_batch(self, batch_result):
        vals = super(AccountPaymentRegister, self)._create_payment_vals_from_batch(
            batch_result
        )
        if self.partner_type == "customer":
            vals["saleperson_id"] = self._get_batch_saleperson(batch_result)
        vals.update(
            {
                "book_no": self.book_no,
                "no": self.no,
                "messenger_name": self.messenger_name.id if self.messenger_name else False,
                "branch_id": self.branch_id.id
            }
        )
        return vals

    @api.model
    def _get_batch_saleperson(self, batch_result):
        move_ids = batch_result["lines"].mapped("move_id")
        if not move_ids:
            return None
        for move in move_ids.sorted(key=lambda m: m.invoice_date):
            return move.invoice_user_id.id