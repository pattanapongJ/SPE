from odoo import api, fields, models


class PDCWizard(models.Model):
    _inherit = 'pdc.wizard'

    area_type = fields.Selection(
        string='Area',
        selection=[('local', 'Local'),
                   ('out_of_town', 'Out of Town')],
        default='local',
        required=False)
