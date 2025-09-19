
from odoo import api, fields, models, _
import re

class AccountMove(models.Model):
    _inherit = "account.move"

    modify_type_txt = fields.Char(string="แปลง/Type/Block") 
    plan_home = fields.Char(string="แบบบ้าน")
    project_name = fields.Many2one('sale.project', string='Project Name')
    customer_po = fields.Char(string="Customer PO")
    room = fields.Char(string="ชั้น/ห้อง")