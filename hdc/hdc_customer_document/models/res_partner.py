# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    cus_doc_id = fields.Many2one('customer.document', string="แบบที่")
    cus_doc_note_1 = fields.Text(string="ชุดที่1", compute="_compute_customer_document", readonly=False, store=True)
    cus_doc_remark_1 = fields.Text(string="หมายเหตุ1", compute="_compute_customer_document", readonly=False, store=True)
    cus_doc_note_2 = fields.Text(string="ชุดที่2", compute="_compute_customer_document", readonly=False, store=True)
    cus_doc_remark_2 = fields.Text(string="หมายเหตุ2", compute="_compute_customer_document", readonly=False, store=True)
    cus_doc_note_3 = fields.Text(string="ชุดที่3", compute="_compute_customer_document", readonly=False, store=True)
    cus_doc_remark_3 = fields.Text(string="หมายเหตุ3", compute="_compute_customer_document", readonly=False, store=True)

    @api.depends("cus_doc_id")
    def _compute_customer_document(self):
        for record in self:
            find_customer_document = self.env['customer.document'].browse(record.cus_doc_id.id)
            if find_customer_document:
                record.cus_doc_note_1 = find_customer_document.note_1
                record.cus_doc_remark_1 = find_customer_document.remark_1
                record.cus_doc_note_2 = find_customer_document.note_2
                record.cus_doc_remark_2 = find_customer_document.remark_2
                record.cus_doc_note_3 = find_customer_document.note_3
                record.cus_doc_remark_3 = find_customer_document.remark_3
            else:
                record.cus_doc_note_1 = ''
                record.cus_doc_remark_1 = ''
                record.cus_doc_note_2 = ''
                record.cus_doc_remark_2 = ''
                record.cus_doc_note_3 = ''
                record.cus_doc_remark_3 = ''