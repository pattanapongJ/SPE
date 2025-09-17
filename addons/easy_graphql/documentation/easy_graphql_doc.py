# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields
from odoo.models import NewId

class EasyGraphQlDoc(models.Model):
    _name = 'easy.graphql.doc'
    _description = 'GraphQl Documentation'

    name = fields.Char('Name')
    easy_api_id = fields.Many2one('easy.api', 'API')
    doc_iframe = fields.Html(string="IFrame", compute='_compute_doc_iframe',sanitize=False)

    def _compute_doc_iframe(self):
        for rec in self:
            if isinstance(rec.id, NewId):
                value = (f'<iframe src="/{rec.easy_api_id.base_endpoint}/graphqldoc/'
                        f'{rec.id.origin}" title="GraphQl Doc" style="width: 100%; '
                        'height: 100%;"/>')
                rec.doc_iframe = value
            else:
                value = (f'<iframe src="/{rec.easy_api_id.base_endpoint}/graphqldoc/{rec.id}" '
                        'title="GraphQl Doc" style="width: 100%; height: 100%;"/>')
                rec.doc_iframe = value

