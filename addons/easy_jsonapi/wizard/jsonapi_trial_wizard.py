# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields, api

class ApiTrialWizard(models.TransientModel):
    _name = 'jsonapi.trial.wizard'
    _description = 'Test JSON-API'

    model_id = fields.Many2one('ir.model', string='Model')
    normal_field_ids = fields.Many2many('ir.model.fields', 'ir_normal_field_rel', string='Normal Fields')
    include_field_ids = fields.Many2many('ir.model.fields', 'ir_include_field_rel', string='Include Fields')
    include_model_ids = fields.Many2many('ir.model', string='Include Model')
    include_model_field_ids = fields.Many2many('ir.model.fields', 'ir_include_model_field_rel', string='Include Model Fields')
    jsonapi_sample = fields.Text('Json-API Sample')
    easy_api_id = fields.Many2one('easy.api')

    @api.onchange('model_id')
    def _onchange_model_id(self):
        for rec in self:
            rec.normal_field_ids = False
            rec.include_field_ids = False
            rec.include_model_ids = False
            rec.include_model_field_ids = False
            rec.jsonapi_sample = False

    @api.onchange('include_field_ids')
    def _onchange_set_include_model_ids(self):
        for rec in self:
            rec.include_model_ids = False
            models_set = set()
            for v in rec.include_field_ids:
                models_set.add(v.relation)
            if models_set:
                ir_models = self.env['ir.model'].sudo().search([('model', 'in', list(models_set))])
                rec.include_model_ids = ir_models

    @api.onchange('normal_field_ids','include_field_ids','include_model_field_ids')
    def _onchange_set_jsonapi_sample(self):
        for rec in self:
            if rec.model_id and rec.normal_field_ids:
                basic_url = f'{rec.easy_api_id.base_url}{rec.easy_api_id.base_endpoint}/{rec.model_id.model}'
                query_parameters = []
                main_field_list = set()

                for field in rec.normal_field_ids:
                    main_field_list.add(field.name)

                if rec.include_field_ids:
                    include_field_list = []
                    for inc_field in rec.include_field_ids:
                        include_field_list.append(inc_field.name)
                    query_parameters.append(f'include={",".join(include_field_list)}')

                if rec.include_model_field_ids:
                    include_model_fields_dict = {}
                    for v in rec.include_model_field_ids:
                        if v.model_id.model == rec.model_id.model:
                            main_field_list.add(v.name)
                        else:
                            include_model_fields_dict[f'{v.model_id.model}'] = f'{include_model_fields_dict[f"{v.model_id.model}"]},{v.name}' if include_model_fields_dict.get(f'{v.model_id.model}') else v.name
                    for key,val in include_model_fields_dict.items():
                        query_parameters.append(f'fields[{key}]={val}')

                query_parameters.append(f'fields[{rec.model_id.model}]={",".join(main_field_list)}')

                main_url = f'{basic_url}?{"&".join(query_parameters)}'
                rec.jsonapi_sample = main_url
            else:
                rec.jsonapi_sample = None
