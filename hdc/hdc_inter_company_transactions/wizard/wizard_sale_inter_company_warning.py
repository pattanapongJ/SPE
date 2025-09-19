from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleInterCompanyWarningWizard(models.TransientModel):
    _name = 'sale.inter.company.warning.wizard'
    _description = 'Sale Inter Company Warning Wizard'

    wizard_id = fields.Many2one('wizard.sale.inter.company', string='Wizard', readonly=True)
    message = fields.Text(string="Message", readonly=True)

    def action_proceed(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.sale.inter.company',
            'res_id': self.wizard_id.id,
            'view_mode': 'form',
            'target': 'new',
            'context': dict(self.env.context, skip_pricelist_check=True),
        }
