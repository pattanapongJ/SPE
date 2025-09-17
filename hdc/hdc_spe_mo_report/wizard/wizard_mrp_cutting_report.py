from pprint import pprint

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WizardMrpCuttingReport(models.TransientModel):
    _name = "wizard.mrp.cutting.report"
    _description = "wizard.mrp.cutting.report"

    mrp_id = fields.Many2one('mrp.production', string='MO')
    state = fields.Char(string='State')

    operation_id = fields.Many2one('mrp.routing.workcenter', 'ส่วนงาน')
    mrp_cutting_line_id = fields.One2many('wizard.mrp.cutting.report.line', 'wizard_mrp_cutting_report_id', string = 'Production state',)
    material_requisition_type_id = fields.Many2one('material.requisition.type', string ='Material Requisition Type')

    def _prepare_report_data(self):
        quantity_qty_lines = []
        quantity_qty_cuts = []
        returned_scrap = []
        for line in self.mrp_cutting_line_id:
            quantity_qty_lines.append(line.quantity_qty_line)
            quantity_qty_cuts.append(line.quantity_qty_cut)
            returned_scrap.append(line.returned_scrap)

        data = {
            'operation_id': self.operation_id.id,
            'mrp_id':self.mrp_id.id,
            'quantity_qty_lines':quantity_qty_lines,
            'quantity_qty_cuts':quantity_qty_cuts,
            'returned_scrap':returned_scrap,
            'material_requisition_type_id':self.material_requisition_type_id.id,
        }
        return data
    
    def print(self):
        self.ensure_one()
        data = self._prepare_report_data()
        mrp_id = self.mrp_id
        operation_id = self.operation_id
        move_raw_ids = mrp_id.move_raw_ids.filtered(lambda x: x.operation_id.id == operation_id.id)
        if not move_raw_ids:
            raise UserError(_("ไม่พบข้อมูลการผลิตสำหรับส่วนงานนี้"))
        return self.env.ref('hdc_spe_mo_report.material_requestion_cutting_template').report_action(self.mrp_id,data=data)
    
class WizardMrpCuttingReportLine(models.TransientModel):
    _name = "wizard.mrp.cutting.report.line"
    _description = "wizard.mrp.cutting.report.line"

    wizard_mrp_cutting_report_id = fields.Many2one('wizard.mrp.cutting.report', 'Mrp Cutting', required=True, ondelete="cascade")
    product_id = fields.Many2one('product.product', 'Product',)
    quantity_qty_line = fields.Float(string='จำนวน (เส้น/kg)', digits='Product Unit of Measure',)
    quantity_qty_cut = fields.Float(string='ตัดขนาด (มม)', digits='Product Unit of Measure',)
    quantity_done = fields.Float(string='จำนวน (ชิ้น)', digits='Product Unit of Measure',)
    returned_scrap = fields.Char(string='เศษส่งคืน (kg)')
