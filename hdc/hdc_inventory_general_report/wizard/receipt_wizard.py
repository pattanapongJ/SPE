# -*- coding: utf-8 -*-
import base64
import io
from odoo import models, fields, api

class WizardReceiptReports(models.TransientModel):
    _name = "wizard.receipt.report"
    _description = "wizard.receipt.report"

    picking_id = fields.Many2one('stock.picking', string='Picking ID')

    receipt_selection =[('receipt_th','ใบรับสินค้า'),
                        ('receipt_en','Product Receipt'),
                        ('receipt_shortage_overage','รายงานใบรับสินค้า ขาด/เกิน')
                        ]
    documents = fields.Selection(receipt_selection,string='Documents')


    def print(self):     
        if self.documents  == 'receipt_th':
            return self.env.ref('hdc_inventory_general_report.receipt_inventory_report_view').report_action(self.picking_id)
        if self.documents  == 'receipt_en':
            return self.env.ref('hdc_inventory_general_report.receipt_inventory_en_report_view').report_action(self.picking_id)
        if self.documents  == 'receipt_shortage_overage':
            return self.env.ref('hdc_inventory_general_report.receipt_shortage_overage_report_view').report_action(self.picking_id)