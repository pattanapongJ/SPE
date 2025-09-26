# -*- coding: utf-8 -*-
import base64
import io
from odoo import models, fields, api

class WizardInterTranfersReports(models.TransientModel):
    _name = "wizard.inter.tranfers.report"
    _description = "wizard.inter.tranfers.report"

    picking_id = fields.Many2one('stock.picking', string='Picking ID')

    inter_tranfers_selection =[('inter_tranfers','ใบโอนย้ายระหว่างคลังสินค้า')
    ,('inter_tranfers_ls','Tranfers'),('inter_tranfers_llk','ใบจัดสินค้าลาดหลุมแก้ว')]
    documents = fields.Selection(inter_tranfers_selection,string='Documents')


    def print(self):     
        if self.documents  == 'inter_tranfers':
            return self.env.ref('hdc_inventory_general_report.inter_tranfer_inventory_report_view').report_action(self.picking_id)
        if self.documents  == 'inter_tranfers_ls':
            return self.env.ref('hdc_inventory_general_report.tranfers_inventory_report_ls_view').report_action(self.picking_id)
        if self.documents  == 'inter_tranfers_llk':
            return self.env.ref('hdc_inventory_general_report.tranfers_inventory_report_llk_view').report_action(self.picking_id)
