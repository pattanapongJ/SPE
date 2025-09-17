from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cash_journal_id = fields.Many2one(comodel_name="account.journal",string="Cash Journal",
                                      domain="[('type', '=', 'cash')]",
                                      config_parameter='hdc_addon_branch_api.default_cash_journal_id',)
