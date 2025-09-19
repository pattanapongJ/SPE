# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
from odoo import api, fields, models, _
from datetime import datetime, timedelta
import requests
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception, Response, root
from odoo.exceptions import AccessError, UserError, AccessDenied, ValidationError
import ast

class SyncDatabaseOrder(models.Model):
    _name = "sync.db.order"
    _description = "Sync Database Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string = "Name")
    json_data = fields.Text(string = "Json", tracking=True)
    type = fields.Selection(selection=[('invoice', 'Invoice'), ('payment_register', 'Payment Register'),
                                       ('payment', 'Payment'),], readonly=True)

    state = fields.Selection(selection = [("draft", "Waiting Create"),
                                          ("error", "Error Create"),
                                          ("error_payment", "Error Payment"),
                                          ("error_invoice_post", "Error Post Invoice"),
                                          ("done", "Success")], string = "Status",
        required = True, default = "draft", copy = False, tracking=True)

    message = fields.Text(string = "Log Message:", tracking=True)

    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    payment_id = fields.Many2one('account.payment', string = 'Payment', readonly = True)
    after_account_id = fields.Integer(string='Invoice ID for create payment')

    def button_create_value(self):
        if self.type == "invoice":
            try:
                json_data = json.loads(self.json_data)
                account = self.env["account.move"].sudo().create(json_data)
                self.invoice_id = account.id
                try:
                    account.action_post()
                    self.message = "Invoice posted successfully."
                    self.state = "done"
                except Exception as post_error:
                    self.message = f"Invoice created but failed to post: {str(post_error)}"
                    self.state = "error_invoice_post"
                    return
            except Exception as e:
                self.message = f"Failed to create invoice: {str(e)}"
                self.state = "error"
                return
        elif self.type == "payment":
            try:
                json_data = json.loads(self.json_data)
                sync_acc = self.browse(self.after_account_id)
                context = {
                    'active_model': 'account.move', 'active_ids': [sync_acc.invoice_id.id],
                    }
                payment = self.env["account.payment.register"].with_context(**context).sudo().create(json_data)
                payment_id = payment._create_payments()
                self.message = "Invoice Payment successfully."
                self.state = "done"
                self.payment_id = payment_id.id
            except Exception as e:
                self.message = f"Failed to create Payment: {str(e)}"
                self.state = "error"