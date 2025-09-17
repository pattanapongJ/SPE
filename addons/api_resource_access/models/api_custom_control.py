# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields, api

class ApiCustomControl(models.Model):
    _name = 'api.custom.control'
    _description = 'API Custom Control'

    name = fields.Char('Name')
    custom_model_access_ids = fields.One2many('custom.model.access', 'api_custom_control_id',
                                              string='Personalized Accesses')
    group_id = fields.Many2one('res.groups', ondelete='restrict', string='Group')
    user_id = fields.Many2one('res.users', ondelete='restrict', string='User')
    ir_model_access_ids = fields.Many2many('ir.model.access', string='Ir Model Access',
                                           ondelete='restrict')
    rule_group_ids = fields.Many2many('ir.rule', related='group_id.rule_groups',
                                      string='Group Rules', readonly=False)

    def action_applied_rules(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'base.action_rule')
        action['domain'] = ['|',('global','=',True),('groups','in',self.group_id.ids),
                            ('model_id','in', self.custom_model_access_ids.model_id.ids)]
        return action

    def write(self, vals):
        result = super().write(vals)
        remove_model_access_ids = []

        if 'custom_model_access_ids' in vals:
            new_vals = {'ir_model_access_ids': []}
            for custom_access in  self.custom_model_access_ids:
                # model access which have to modified
                if custom_access.model_id in self.ir_model_access_ids.model_id:
                    rec_vals = {
                        'perm_read': custom_access.read_perm,
                        'perm_write': custom_access.write_perm,
                        'perm_create': custom_access.create_perm,
                        'perm_unlink': custom_access.delete_perm,
                    }
                    for i in self.ir_model_access_ids:
                        if i.model_id == custom_access.model_id:
                            i.write(rec_vals)

                else: # model access which have to create new
                    rec_vals = {
                        'name': f'{self.name}_{custom_access.model_id.model}',
                        'model_id': custom_access.model_id.id,
                        'group_id': self.group_id.id,
                        'perm_read': custom_access.read_perm,
                        'perm_write': custom_access.write_perm,
                        'perm_create': custom_access.create_perm,
                        'perm_unlink': custom_access.delete_perm,
                    }
                    new_model_access_id = self.env['ir.model.access'].create(rec_vals).id
                    new_vals['ir_model_access_ids'].append([4, new_model_access_id, False])

            # model access which have to delete
            for ir_access in self.ir_model_access_ids:
                # model access which have to delete
                if ir_access.model_id not in self.custom_model_access_ids.model_id:
                    self.group_id.write({'model_access': [[3, ir_access.id, False]]})
                    new_vals['ir_model_access_ids'].append([3, ir_access.id, False])
                    remove_model_access_ids.append(ir_access.id)

            result = super().write(new_vals)

            # Delete unwanted model accesses
            if remove_model_access_ids:
                remove_model_access = self.ir_model_access_ids.browse(remove_model_access_ids)
                remove_model_access.unlink()

        return result

    @api.model_create_multi
    def create(self, vals):

        for val in vals:
            # CREATE GROUP
            group_id = self.env['res.groups'].create({'name': val['name']})
            val['group_id'] = group_id.id

            # CREATE USER
            user_val = {
                'login': f'{val["name"]}_BOT',
                'name': f'{val["name"]}_BOT',
                'groups_id': [group_id.id],
                'is_personalized_access': True,
                'active': True
            }
            user_id = self.env['res.users'].create(user_val)
            val['user_id'] = user_id.id

        result = super().create(vals)

        # CREATE ir_model_access
        model_access_ids = []
        for rec in result.custom_model_access_ids:
            rec_vals = {
                'name': f'{result.name}_{rec.model_id.model}',
                'model_id': rec.model_id.id,
                'group_id': group_id.id,
                'perm_read': rec.read_perm,
                'perm_write': rec.write_perm,
                'perm_create': rec.create_perm,
                'perm_unlink': rec.delete_perm,
            }
            model_access_id = self.env['ir.model.access'].create(rec_vals).id
            model_access_ids.append(model_access_id)

        result.write({'ir_model_access_ids': model_access_ids})

        return result

    def unlink(self):
        rule_ids = self.rule_group_ids
        group_id = self.group_id
        user_id = self.user_id
        ir_model_access_ids = self.ir_model_access_ids
        custom_model_access_ids = self.custom_model_access_ids

        vals = {
            'group_id': [(5, 0 ,0)],
            'user_id': [(5, 0 ,0)],
            'ir_model_access_ids': [(5, 0 ,0)],
            'custom_model_access_ids': [(5, 0 ,0)],
        }

        self.write(vals)

        group_vals = {'model_access': [(5, 0 ,0)]}
        group_id.write(group_vals)

        user_vals = {'groups_id': [(5, 0 ,0)]}
        user_id.write(user_vals)

        model_access_vals = {'group_id': [(5, 0 ,0)]}
        ir_model_access_ids.write(model_access_vals)

        rule_ids.unlink()
        group_id.unlink()
        user_id.unlink()
        ir_model_access_ids.unlink()
        custom_model_access_ids.unlink()

        return super().unlink()

