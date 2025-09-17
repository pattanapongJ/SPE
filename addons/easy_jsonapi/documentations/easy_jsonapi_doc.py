# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields, api
from odoo.models import NewId

class EasyJsonApiDoc(models.Model):
    _name = 'easy.jsonapi.doc'
    _description = 'JsonApi Documentation'

    name = fields.Char('Name')
    easy_api_id = fields.Many2one('easy.api', 'API')
    model_ids = fields.Many2many('ir.model', string='Models')
    doc_iframe = fields.Html(string="IFrame", compute='_compute_doc_iframe',sanitize=False)

    @api.depends('model_ids')
    def _compute_doc_iframe(self):
        for rec in self:
            if isinstance(rec.id, NewId):
                result = rec.env['easy.jsonapi.doc'].browse(rec.id.origin).write(
                                                                    {'model_ids':rec.model_ids.ids})
                value = (f'<iframe src="/{rec.easy_api_id.base_endpoint}/jsonapidoc/'
                         f'{rec.id.origin}" title="JsonAPI Doc" '
                         'style="width: 100%; height: calc(100vh - 100px);"/>')
                rec.doc_iframe = value
            else:
                value = (f'<iframe src="/{rec.easy_api_id.base_endpoint}/jsonapidoc/{rec.id}" '
                         'title="JsonAPI Doc" style="width: 100%; height: calc(100vh - 100px);"/>')
                rec.doc_iframe = value

