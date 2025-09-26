from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardMrpReport(models.TransientModel):
    _name = "wizard.mrp.report"
    _description = "wizard.mrp.report"

    document = fields.Selection([
        ("material_requestion", "ใบเบิก/ขอเบิก"),
        ("material_requestion_cutting", "ใบเบิก/ตัดวัตถุดิบ"),
        ("mrp_production_state", "ใบรายงานสถานะการผลิต"),
        ("mrp_fg_ls", "ใบรับผลิตเสร็จ"),
        ("mrp_production_order", "ใบสั่งผลิต"),
    ],
    string="Documents"
    )

    mrp_id = fields.Many2one('mrp.production', string='MO')
    state = fields.Char(string='State')

    operation_id = fields.Many2one('mrp.routing.workcenter', 'ส่วนงาน')
    material_requisition_type_id = fields.Many2one('material.requisition.type', string ='Material Requisition Type')
    
    def _prepare_report_data(self):
        data = {
            'operation_id': self.operation_id.id,
            'mrp_id':self.mrp_id.id,
            'material_requisition_type_id':self.material_requisition_type_id.id
        }
        return data
    
    def _prepare_report_data_mrp_production_state(self):
        data = {
            'mrp_id':self.mrp_id.id,
        }
        return data
    
    def _prepare_mrp_cutting_report_data(self):
        product_list = []
        for move in self.mrp_id.move_raw_ids:
            if self.operation_id:
                if move.operation_id.id == self.operation_id.id:
                    data_dict = (0,0,{
                    "product_id":move.product_id.id,
                    "quantity_done":move.quantity_done,})
                    product_list.append(data_dict)
            else:
                data_dict = (0,0,{
                    "product_id":move.product_id.id,
                    "quantity_done":move.quantity_done,})
                product_list.append(data_dict)
        return product_list

    
    # def create_mrp_cutting_report(self):
    #     self.ensure_one()
    #     product_list = self._prepare_mrp_cutting_report_data()
    #     return {
    #             "name": "ใบเบิก/ตัดวัตถุดิบ",
    #             "type": "ir.actions.act_window",
    #             "res_model": "wizard.mrp.cutting.report",
    #             "view_mode": 'form',
    #             'target': 'new',
    #             "context": {"default_mrp_id": self.mrp_id.id,
    #                         "default_operation_id": self.operation_id.id,
    #                         "default_mrp_cutting_line_id": product_list,},
    #         }
    
    def print(self):
        self.ensure_one()
        mrp_id = self.mrp_id
        operation_id = self.operation_id
        if operation_id:
            move_raw_ids = mrp_id.move_raw_ids.filtered(lambda x: x.operation_id.id == operation_id.id)
            if not move_raw_ids:
                raise UserError(_("ไม่พบข้อมูลการผลิตสำหรับส่วนงานนี้"))
        if self.document == "material_requestion":
            data = self._prepare_report_data()
            return self.env.ref('hdc_spe_mo_report.material_requestion_template').report_action(self.mrp_id,data=data)
        if self.document == "material_requestion_cutting":
            product_list = self._prepare_mrp_cutting_report_data()
            return {
                "name": "ใบเบิก/ตัดวัตถุดิบ",
                "type": "ir.actions.act_window",
                "res_model": "wizard.mrp.cutting.report",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_mrp_id": self.mrp_id.id,
                            "default_operation_id": self.operation_id.id,
                            "default_mrp_cutting_line_id": product_list,
                            "default_material_requisition_type_id":self.material_requisition_type_id.id},
            }
        if self.document == "mrp_production_state":
            data = self._prepare_report_data_mrp_production_state()
            mrp_production_state_ids = self.env["mrp.production.state"].search([('mrp_id','=',mrp_id.id)])
            if not mrp_production_state_ids:
                raise UserError(_("ไม่พบข้อมูลการผลิตสำหรับเลขที่สั่งผลิตนี้"))
            return self.env.ref('hdc_spe_mo_report.mrp_production_state_template').report_action(self.mrp_id,data=data)
        if self.document == "mrp_fg_ls":
            data = self._prepare_report_data_mrp_production_state()
            return self.env.ref('hdc_spe_mo_report.action_report_mrp_fg_ls').report_action(self.mrp_id,data=data)
        if self.document == "mrp_production_order":
            data = self._prepare_report_data_mrp_production_state()
            return self.env.ref('mrp.action_report_production_order').report_action(self.mrp_id)