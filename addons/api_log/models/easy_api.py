# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields
from odoo.tools import config

class EasyApi(models.Model):
    _inherit = 'easy.api'

    logfile = fields.Text('Log File', compute='_compute_logfile')

    def action_log(self):
        action = self.env['ir.actions.act_window']._for_xml_id('api_log.action_open_wizard_api_log')
        action['context'] = {'default_easy_api_id': self.id}
        return action

    def _compute_logfile(self):
        for rec in self:
            rec.logfile = self.get_logfile(mode='easy')

    def get_logfile(self, mode):
        # When api_mode is easy
        if mode == 'easy':
            return config.get('logfile')

        # When api_mode is advance
        elif mode == 'advance':
            return config.get('logfile')

