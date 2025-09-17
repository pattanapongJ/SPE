from odoo import api, models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    is_group_account = fields.Boolean(string='Group By Account', default=True, help="Enable to group journal items by account in the journal entries.")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        Config = self.env['ir.config_parameter'].sudo()
        is_group_account = Config.get_param("is_group_account", default="")
        res.update({
            'is_group_account': is_group_account,
        })
        return res
    
    @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        Config = self.env['ir.config_parameter'].sudo()
        Config.set_param("is_group_account", self.is_group_account)