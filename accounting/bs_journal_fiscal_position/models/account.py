from odoo import api,fields,models

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position', readonly=True,
        states={'draft': [('readonly', False)]},
        check_company=True,
        domain="[('company_id', '=', company_id)]", ondelete="restrict",
        help="Fiscal positions are used to adapt taxes and accounts for particular customers or sales orders/invoices. "
             "The default value comes from the customer.", compute='_compute_fiscal_position', store=True)
    
    @api.depends('journal_id')
    def _compute_fiscal_position(self):
        # if not self.fiscal_position_id:
        self.fiscal_position_id = self.journal_id.fiscal_pos_id
        