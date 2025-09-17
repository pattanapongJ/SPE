# -*- coding: utf-8 -*-
######################################################################
#                                                                    #
# Part of EKIKA CORPORATION PRIVATE LIMITED (Website: ekika.co).     #
# See LICENSE file for full copyright and licensing details.         #
#                                                                    #
######################################################################

from odoo import models, fields

class ApiCustomModelAccess(models.Model):
    _name = 'custom.model.access'
    _description = 'API Custom Model Access'

    api_custom_control_id = fields.Many2one('api.custom.control')
    model_id = fields.Many2one('ir.model', 'Model')
    create_perm = fields.Boolean('Create')
    read_perm = fields.Boolean('Read')
    write_perm = fields.Boolean('Write')
    delete_perm = fields.Boolean('Delete')
