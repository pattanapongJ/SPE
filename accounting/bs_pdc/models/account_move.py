from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'


    def open_rc_pdc_payment(self):
        action = self.env.ref('sh_pdc.sh_pdc_payment_menu_action').read()[0]
        form_view = [(self.env.ref('sh_pdc.sh_pdc_payment_form_view').id, 'form')]
        action['views'] = form_view
        action['res_id'] = self.pdc_id.id
        return action

