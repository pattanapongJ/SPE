from odoo import api, fields, models
from odoo.osv import expression


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'



    offset_move_line_id = fields.Many2one('account.move.line',string='Offset Move Line',copy=False)


    def action_reconcile_with_offset_move_line(self):
        for line in self.filtered(lambda x:x.offset_move_line_id and not x.display_type and x.parent_state == 'posted'):
            if line.offset_move_line_id:
                (line.offset_move_line_id + line).with_context(skip_account_move_synchronization=True).reconcile()


    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):

        if operator == 'ilike':
            domain = ['|', '|',
                      ('name', 'ilike', name),
                      ('move_id', 'ilike', name),
                      ('product_id', 'ilike', name)]
            if self._context.get('search_gl_items'):
                domain = ['|', '|','|',
                          ('name', 'ilike', name),
                          ('move_id', 'ilike', name),
                          ('product_id', 'ilike', name),
                          ('account_id', 'ilike', name)]

            return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

        return super()._name_search(name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)






