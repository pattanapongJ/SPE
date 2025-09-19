from odoo import api, fields, models
from odoo.exceptions import UserError

class InventoryAdjustmentType(models.Model):
    _name = 'inventory.adjustment.type'
    _description = 'Inventory Adjustment Type'

    name = fields.Char(string='Type Inventory Adjustment', required=True)

    company_id = fields.Many2one(
        'res.company', string='Company', required=True, ondelete='cascade')

    type_action = fields.Selection(
        selection=[
            ("count_stock", "ตรวจนับ"),
            ("edit_stock", "ปรับปรุงสต๊อก")
        ],
        string="Type",
        default="count_stock"
    )

    sequence_id = fields.Many2one('ir.sequence', string='Sequence',
                                  required=True,
                                  domain="[('code', '=', 'inventory_adjustment') , ('company_id', '=', False)]",
                                  help='The sequence used for generating inventory references.'
    )

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            return {
                'domain': {
                    'sequence_id': [
                        ('code', '=', 'inventory_adjustment'),
                        ('company_id', '=', self.company_id.id)
                    ]
                }
            }
        else:
            self.sequence_id = False
            return {
                'domain': {
                    'sequence_id': [('code', '=', 'inventory_adjustment') , ('company_id', '=', False)]
                }
            }





    
    # inventory_ref = fields.Char(
    #     string='Inventory Reference',
    #     compute='_compute_inventory_ref',
    #     store=False,
    #     help='Preview of the next sequence number for the selected company'
    # )

    # @api.depends('company_id')
    # def _compute_inventory_ref(self):
    #     """Compute a preview of the sequence based on company"""
    #     for record in self:
    #         record.inventory_ref = ''
    #         if record.company_id:
    #             sequence_code = 'inventory_adjustment'
    #             sequence = self.env['ir.sequence'].sudo().search([
    #                 ('code', '=', sequence_code),
    #                 ('company_id', '=', record.company_id.id)
    #             ], limit=1)

    #             if sequence:
    #                 record.inventory_ref = sequence.preview
    #             else:
    #                 record.inventory_ref = ""
