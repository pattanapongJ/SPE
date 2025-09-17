# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields, api

HELP_JSONAPI_BODY_GET = '''Enable this feature when you want to use body in GET requests of Json:API.

Note: jsonapi.org specification says use query params for GET requests. Also it goes against the HTTP/1.1 specification and is generally discouraged.

Server restart may require for this change.
'''

class EasyApi(models.Model):
    _inherit = 'easy.api'

    api_type = fields.Selection(selection_add=[('jsonapi','JSON-API')])
    easy_jsonapi_doc_id = fields.Many2one('easy.jsonapi.doc', 'Json API Doc')
    jsonapi_use_body_for_get = fields.Boolean('Data in Body', help=HELP_JSONAPI_BODY_GET)

    # Meta Information
    meta_author_name = fields.Char(string='Author', help=('It is used in the meta information of '
                                                          'JsonAPI to describe the author name.'))
    meta_author_email = fields.Char(string='Author Email',
                                    help=('It is used in the meta information '
                                          'of JsonAPI to describe the author\'s email.'))
    meta_documentation_link = fields.Text(string='Docuementation Link',
                                          help=('It is used in the meta information of JsonAPI to '
                                                'indicate the documentation link.'))

    def action_jsonapi_doc(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'easy_jsonapi.action_easy_jsonapi_doc')
        action['res_id'] = self.easy_jsonapi_doc_id.id
        action['view_mode'] = 'form'
        action['views'] = [[self.env.ref('easy_jsonapi.view_easy_jsonapi_doc_form').id, 'form']]
        return action

    @api.model_create_multi
    def create(self, vals_list):
        results = super().create(vals_list)
        for result in results:
            if result.api_type == 'jsonapi':
                doc = self.env['easy.jsonapi.doc'].create({
                    'name': f'{result.name}_DOC',
                    'easy_api_id': result.id
                    })
                result.easy_jsonapi_doc_id = doc.id
        return results

    def write(self, vals):
        api_type = vals.get('api_type')
        if api_type:
            if api_type == 'jsonapi':
                if not self.easy_jsonapi_doc_id:
                    doc = self.env['easy.jsonapi.doc'].create({
                        'name': f'{self.name}_DOC',
                        'easy_api_id': self.id
                        })
                    self.easy_jsonapi_doc_id = doc.id
            else:
                if self.easy_jsonapi_doc_id:
                    self.easy_jsonapi_doc_id.unlink()
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record.easy_jsonapi_doc_id:
                record.easy_jsonapi_doc_id.unlink()
        return super().unlink()

    def jsonapi_url_maker(self):
        action = self.env['ir.actions.act_window']\
                 ._for_xml_id('easy_jsonapi.action_jsonapi_trial_wizard')
        action['context'] = {'default_easy_api_id': self.id}
        return action

    @api.depends('api_type')
    def _compute_api_type_help(self):
        super()._compute_api_type_help()
        for rec in self:
            if rec.api_type == 'jsonapi':
                help_msg = ('<b>Api Type</b>: This field describe which type of api you are going '
                            'to use, currently it is JSON-API, For more Details Go to: '
                            '<a href="https://jsonapi.org/format/1.1/" target="_blank" class="" '
                            'data-bs-original-title="" title="">Json-APi Specification')
                rec.api_type_help = help_msg

