# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import requests
from odoo.exceptions import Warning
import json

class SyncAppList(models.Model):
    _name = "sync.app.list"
    _description = "Sync List"

    name = fields.Char(string = "Name")
    state = fields.Selection(
        selection = [("draft", "Not Connected"),
                     ("connect", "Connected")],
        string = "Status", required = True, default = "draft", copy = False)
    endpoint_url = fields.Char(string = "Endpoint Url:", required=True)
    apikey = fields.Char(string = "API Key", required=True)
    instance_db = fields.Char(string = "Database", required=True)
    log_note = fields.Text(string = "Log Note")

    invoice = fields.Boolean(string = "Invoice", default = False, Copy = False)
    invoice_ids = fields.One2many('invoice.sync.line', 'sync_id', string = "Invoice Fields", Copy = False)
    invoice_domain = fields.Char(string = "Invoice Domain")

    payment = fields.Boolean(string = "Payment", default = False, Copy = False)
    payment_ids = fields.One2many('payment.sync.line', 'sync_id', string = "Payment Fields", Copy = False)
    payment_domain = fields.Char(string = "Payment Domain")

    @api.onchange('invoice')
    def _onchange_invoice(self):
        """ เมื่อ invoice = True ให้สร้างไลน์รายการฟิลด์ของ account.move """
        if self.invoice:
            self.invoice_ids = [(5, 0, 0)]  # ล้างค่าเก่าออกก่อน
            model_fields = self.env['ir.model.fields'].search([('model', '=', 'account.move')])
            lines = []
            for field in model_fields:
                if field.required:
                    lines.append((0, 0, {
                        'sync': True,
                        'field_id': field.id,
                    }))
                else:
                    lines.append((0, 0, {
                        'field_id': field.id,
                        }))
            self.invoice_ids = lines

    @api.onchange('payment')
    def _onchange_payment(self):
        """ เมื่อ invoice = True ให้สร้างไลน์รายการฟิลด์ของ account.payment.register """
        if self.payment:
            self.payment_ids = [(5, 0, 0)]  # ล้างค่าเก่าออกก่อน
            model_fields = self.env['ir.model.fields'].search([('model', '=', 'account.payment.register')])
            lines = []
            for field in model_fields:
                lines.append((0, 0, {
                    'sync': True, 'field_id': field.id,
                    }))
            self.payment_ids = lines

class InvoiceSyncLine(models.Model):
    _name = "invoice.sync.line"
    _description = "Invoice Sync Line"
    _order = "sync desc"

    sync_id = fields.Many2one('sync.app.list', string="Sync Ref", ondelete="cascade")
    sync = fields.Boolean(string = "Sync", default = False, Copy = False)
    field_id = fields.Many2one('ir.model.fields', domain = "[('model', '=', 'account.move')]", ondelete = "cascade",required = True)
    field_name = fields.Char(related="field_id.name", string="Name")
    field_type = fields.Selection(related="field_id.ttype", string="Type")

class PaymentSyncLine(models.Model):
    _name = "payment.sync.line"
    _description = "Payment Sync Line"
    _order = "sync desc"

    sync_id = fields.Many2one('sync.app.list', string="Sync Ref", ondelete="cascade")
    sync = fields.Boolean(string = "Sync", default = False, Copy = False)
    field_id = fields.Many2one('ir.model.fields', domain = "[('model', '=', 'account.payment')]", ondelete = "cascade",required = True)
    field_name = fields.Char(related="field_id.name", string="Name")
    field_type = fields.Selection(related="field_id.ttype", string="Type")

