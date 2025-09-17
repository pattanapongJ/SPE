# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, tools, _
from odoo.osv import expression

class AccountMove(models.Model):
    _inherit = "account.move"

    claim_id = fields.Many2one('crm.claim.ept', string='Claim')
    is_job_no = fields.Char(string="Job No.")
    customer_requisition = fields.Char(string='Customer Requisition')
    customer_ref = fields.Char(string='Customer Reference')
    original_value = fields.Float(string='มูลค่าเดิม', copy=False,digits="Product Price")

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = ['|', 
                ('name', operator, name),('form_no', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
 
    @api.depends('name', 'state')
    def name_get(self):
        result = []
        for move in self:
            if self._context.get('name_groupby'):
                name = '**%s**, %s' % (format_date(self.env, move.date), move._get_move_display_name())
                if move.ref:
                    name += '     (%s)' % move.ref
                if move.form_no:
                    name += ' (%s)' % move.form_no
                if move.partner_id.name:
                    name += ' - %s' % move.partner_id.name
            else:
                name = move._get_move_display_name(show_ref=True)
                if move.form_no:
                    name += ' (%s)' % move.form_no
            result.append((move.id, name))
        return result
    
