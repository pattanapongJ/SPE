# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from datetime import datetime

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Costing Fields (TH)
    costing_th = fields.Text(string="ข้อสรุป/Costing (TH)")
    ocpb_th = fields.Text(string="สคบ. (TH)")
    cost_description = fields.Text(string="1.คำอธิบาย")
    detail = fields.Text(string="2.รายละเอียด")
    feature = fields.Text(string="3.คุณสมบัติ")
    how_to_use = fields.Text(string="4.วิธีใช้")
    tip = fields.Text(string="5.ข้อเสนอแนะ")
    warning = fields.Text(string="6.คำเตือน")
    sh1_pro_cost = fields.Text(string="7.SH1-Pro")


    # Costing Fields (EN)
    costing_en = fields.Text(string="ข้อสรุป/Costing (EN)")
    ocpb_en = fields.Text(string="สคบ. (EN)")
    sh1_date_end = fields.Char(string="7.SH1-วันที่เริ่มต้น/สิ้นสุด")
    date_start_and_end = fields.Char(string="วันที่เริ่มต้น/สิ้นสุด")
    recommend_sell_other_provinces = fields.Char(string="แนะนำขาย ตจว.")
    recommend_sell_upvc = fields.Char(string="แนะนำขาย UPVC")


    # Promotion & Cost
    promotion_pc = fields.Char(string="Promotion ตจว. PC")
    other_province_cost = fields.Float(string="ทุนส่ง ตจว.")
    upvc_cost = fields.Float(string="ทุนส่ง UPVC (TH)")
    costumer = fields.Char(string="ชื่อลูกค้า")

    # Product Identification Fields
    pc_no = fields.Char(string="1.PC-No")
    pc_pro = fields.Char(string="1.PC-Pro")
    pc_updated = fields.Char(string="1.PC-วันที่เริ่มต้น/สิ้นสุด")

    sh1_no = fields.Char(string="3.SH1-No")
    sh1_pro = fields.Char(string="3.SH1-Pro")
    sh1_updated = fields.Char(string="3.SH1-วันที่เริ่มต้น/สิ้นสุด")

    sh3_no = fields.Char(string="6.SH3-No")
    sh3_pro = fields.Char(string="6.SH3-Pro")
    sh3_updated = fields.Char(string="6.SH3-วันที่เริ่มต้น/สิ้นสุด")

    sd_no = fields.Char(string="2.SD-No")
    sd_pro = fields.Char(string="2.SD-Pro")
    box_per_unit = fields.Float(string="2.ยก BOX/ชิ้น")
    cnt_per_unit = fields.Float(string="2.ยก CNT/ชิ้น")
    sd_updated = fields.Char(string="2.SD-วันที่เริ่มต้น/สิ้นสุด")

    su_no = fields.Char(string="5.SU-No")
    su_pro = fields.Char(string="5.SU-PRO")
    su_updated = fields.Char(string="5.SU-วันที่เริ่มต้น/สิ้นสุด")

    rsp_normal = fields.Float(string="Rsp-Normal")

    how_to_use_th = fields.Char(string='3.1 วิธีใช้ (TH)')
    how_to_use_en = fields.Char(string='3.2 วิธีใช้ (EN)')
    suggestion_th = fields.Char(string='3.3 คำแนะนำ/คำเตือน (TH)')
    suggestion_en = fields.Char(string='3.4 คำแนะนำ/คำเตือน (EN)')
    material_th = fields.Char(string='3.5 วัสดุ (TH)')
    material_en = fields.Char(string='3.6 วัสดุ (EN)')
    highlights_th = fields.Char(string='3.7 จุดเด่น (TH)')
    highlights_en = fields.Char(string='3.8 จุดเด่น (EN)')
    props_th = fields.Char(string='3.9 คุณสมบัติ (TH)')
    props_en = fields.Char(string='3.10 คุณสมบัติ (EN)')





