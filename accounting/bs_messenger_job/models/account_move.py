# -*- encoding: utf-8 -*-
from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    messenger_job_id = fields.Many2one('messenger.job', string='Messenger Job', copy=False, readonly=True)