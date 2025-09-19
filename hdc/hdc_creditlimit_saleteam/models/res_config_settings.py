# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_credit_limit = fields.Float(string="Default Credit Limit", default_model='res.partner',  default=40000.00)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("hdc_creditlimit_saleteam.default_credit_limit", str(self.default_credit_limit))

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['default_credit_limit'] = float(self.env['ir.config_parameter'].sudo().get_param('hdc_creditlimit_saleteam.default_credit_limit', default=40000.00))
        return res
