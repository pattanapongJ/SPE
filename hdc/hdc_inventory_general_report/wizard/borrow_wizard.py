# -*- coding: utf-8 -*-
import base64
import io
from odoo import models, fields, api

class WizardBorrowReports(models.TransientModel):
    _name = "wizard.borrow.report"
    _description = "wizard.borrow.report"

    picking_id = fields.Many2one('stock.picking', string='Picking ID')

    borrow_selection =[('borrow','ใบเบิกยืมสินค้า (แนวตั้ง)'),('borrow_ls','ใบเบิกยืมสินค้า (แนวนอน)')]
    documents = fields.Selection(borrow_selection,string='Documents')

    delivery_note_selection =[('delivery_note','ใบส่งสินค้าตัวอย่าง'),('delivery_note_pre_preprint','ใบส่งสินค้าตัวอย่าง (Pre Print)')]
    documents_delivery_note = fields.Selection(delivery_note_selection,string='Documents')

    is_delivery_note = fields.Boolean(default=False,string="Is Delivery Note")

    def print(self):
        if self.is_delivery_note:
            if self.documents_delivery_note  == 'delivery_note':
                return self.env.ref('hdc_inventory_general_report.inventory_borrow_report_view').report_action(self.picking_id)
            if self.documents_delivery_note  == 'delivery_note_pre_preprint':
                return self.env.ref('hdc_inventory_general_report.inventory_borrow_new_report_view').report_action(self.picking_id)
        else:
            if self.documents  == 'borrow':
                return self.env.ref('hdc_inventory_general_report.requestion_inventory_report_view').report_action(self.picking_id)
            if self.documents  == 'borrow_ls':
                return self.env.ref('hdc_inventory_general_report.requestion_inventory_report_ls_view').report_action(self.picking_id)
