# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields

class EasyApiCustomAccess(models.Model):
    _inherit = 'easy.api'

    resource_control_type = fields.Selection(
        selection_add=[('custom_access', 'Personalized Access')])
    resource_control_id = fields.Many2one('api.custom.control', 'Personalized Access',
                                         readonly=True)

    def action_generate_custom_access_record(self):
        """
        This action button method is used to create custom control record
        and assign this record to resource_control_id if this field is empty.
        """
        if not self.resource_control_id and self.resource_control_type == 'custom_access':
            resource_control = self.env['api.custom.control'].create({
                'name': f'{self["name"]} Personalized Access'
            })
            self.resource_control_id = resource_control.id

    def action_open(self):
        super().action_open()
        self.action_generate_custom_access_record()

    def action_open_custom_access_record(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'api_resource_access.action_api_custom_control')
        action['res_id'] = self.resource_control_id.id
        action['view_mode'] = 'form'
        # action['target'] = 'new' # for popup window
        action['views'] = [
            [self.env.ref('api_resource_access.view_api_custom_control_form').id, 'form']]
        action['context'] = {'dialog_size': 'xl',}
        return action

    def unlink(self):
        for record in self:
            record.resource_control_id.unlink()
        return super(EasyApiCustomAccess, self).unlink()
