# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields, api

class ApiLog(models.TransientModel):
    _name = 'api.log'
    _description = 'API Log'

    easy_api_id = fields.Many2one('easy.api', 'API')
    iframe_html = fields.Html(string="IFrame")
    logfile = fields.Text('Log File', related='easy_api_id.logfile')

    @api.model
    def default_get(self, default_fields):
        vals = super(ApiLog, self).default_get(default_fields)
        if vals.get("easy_api_id"):
            value = (f'<iframe src="/api/log/{vals["easy_api_id"]}/20" '
                     'title="API Log" colspan="1" class="w-100 h-100" style="min-height: 60vh;"/>')
            vals['iframe_html'] = value
        return vals

