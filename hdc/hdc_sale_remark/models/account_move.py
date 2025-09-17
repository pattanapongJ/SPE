# -*- coding: utf-8 -*-
from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    remark = fields.Text(string="Remark", tracking=True,) 
    remark_report = fields.Text(string="Remark Report", tracking=True,) 