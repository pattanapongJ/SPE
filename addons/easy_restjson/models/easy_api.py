# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields, api

class EasyApi(models.Model):
    _inherit = 'easy.api'

    api_type = fields.Selection(selection_add=[('rest_json','Standard RESTful JSON')])

    @api.depends('api_type')
    def _compute_api_type_help(self):
        super()._compute_api_type_help()
        for rec in self:
            if rec.api_type == 'rest_json':
                help_msg = ('<b>Api Type</b>: This field describe which type of api you are '
                            'going to use, currently it is Standard RESTful JSON')
                rec.api_type_help = help_msg
