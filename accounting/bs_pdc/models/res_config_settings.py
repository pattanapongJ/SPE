from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_automatic_pdc_creation = fields.Boolean(string='Generate PDC automatically',config_parameter='bs_pdc.allow_automatic_pdc_creation')
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        allow_automatic_pdc_creation = params.get_param('bs_pdc.allow_automatic_pdc_creation', default=False)
        res.update(
            allow_automatic_pdc_creation=allow_automatic_pdc_creation
        )
        return res
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        # Fetch the value from `ir.config_parameter`
        res.update(
            allow_automatic_pdc_creation=self.env['ir.config_parameter'].sudo().get_param('bs_pdc.allow_automatic_pdc_creation', default=False)
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        # Save the value to `ir.config_parameter`
        self.env['ir.config_parameter'].sudo().set_param('bs_pdc.allow_automatic_pdc_creation', self.allow_automatic_pdc_creation)
