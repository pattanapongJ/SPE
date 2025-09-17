# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    operation_type_setting_id = fields.Many2one('stock.picking.type', string="Operation Type")
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("hdc_tms.operation_type_setting_id",self.operation_type_setting_id.id)
    
    @api.model
    def default_get(self, fields):
        defaults = super(ResConfigSettings, self).default_get(fields)
        # operation_type_id = self.env.ref('hdc_tms.operation_type_resupply_product')
        # defaults['operation_type_setting_id'] = operation_type_id.id if operation_type_id else False
        return defaults
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['operation_type_setting_id'] = int(self.env['ir.config_parameter'].sudo().get_param('hdc_tms.operation_type_setting_id'))
        
        return res

