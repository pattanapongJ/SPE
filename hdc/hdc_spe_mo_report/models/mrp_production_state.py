from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import time, datetime, timedelta



class MrpProductionState(models.Model):
    _name = 'mrp.production.state'

    mrp_id = fields.Many2one('mrp.production', string='MO')
    worker = fields.Char(string='ผู้ปฏิบัติงาน', required=True)
    date = fields.Date(string='วันที่')
    operation_id = fields.Many2one('mrp.routing.workcenter', 'ขั้นตอน')
    machines_id = fields.Many2one("mrp.machines", "MC No.",)
    work_shifts = fields.Selection([('morning_shift', 'กะเช้า'), ('afternoon_shift ', 'กะบ่าย'),('ot_shift', 'OT')],string="ผลัดเวลาทำงาน", default='morning_shift')
    set_up_start_time= fields.Float(string="Start Set Up")
    set_up_end_time = fields.Float(string="End Set Up")
    production_start_time= fields.Float(string="Start Production")
    production_end_time = fields.Float(string="End Production")
    product_good_qty = fields.Float(string="จำนวนของดี")
    product_failed_qty = fields.Float(string="จำนวนของเสีย")

    @api.onchange("worker")
    def get_domain_workorder_id(self):
        id_list = []       
        for workorder in self.mrp_id.workorder_ids:
            id_list.append(workorder.operation_id.id)

        domain_operation_id = [('id', 'in', id_list)] 
        return {'domain':{'operation_id':domain_operation_id}}
    
    @api.onchange("operation_id")
    def get_domain_workorder_id(self):
        machines_id = []
        self.machines_id = False
        for workorder in self.mrp_id.workorder_ids:
            if workorder.operation_id.id == self.operation_id.id:
                machines_id = workorder.machines_id
        if machines_id:
            self.machines_id = machines_id.id
    
    def name_get(self):
        res = []
        for rec in self:
            name = 'รายงานสถานะการผลิต [%s]'%rec.mrp_id.name + rec.worker
            res.append((rec.id, name))
        return res
    
    def print(self):
        pass