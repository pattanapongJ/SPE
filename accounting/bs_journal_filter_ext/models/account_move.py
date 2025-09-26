from odoo import api, fields,_, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    @api.model
    def _search_default_journal(self, journal_types):
        move_type = self._context.get('default_move_type', 'entry')
        if move_type not in ['in_refund', 'out_refund']:
            return super()._search_default_journal(journal_types)
        
        company_id = self._context.get('default_company_id', self.env.company.id)
        domain = [('company_id', '=', company_id), ('type', 'in', journal_types),('show_in_credit_note', '=', True)]
        journal = None
        if self._context.get('default_currency_id'):
            currency_domain = domain + [('currency_id', '=', self._context['default_currency_id'])]
            journal = self.env['account.journal'].search(currency_domain, limit=1)

        if not journal:
            journal = self.env['account.journal'].search(domain, limit=1)

        if not journal:
            company = self.env['res.company'].browse(company_id)

            error_msg = _(
                "No journal could be found in company %(company_name)s for any of those types: %(journal_types)s",
                company_name=company.display_name,
                journal_types=', '.join(journal_types),
            )
            raise UserError(error_msg)

        return journal
    

    @api.depends('company_id', 'invoice_filter_type_domain')
    def _compute_suitable_journal_ids(self):
        res = super()._compute_suitable_journal_ids()
        for m in self:
            journal_type = m.invoice_filter_type_domain or 'general'
            company_id = m.company_id.id or self.env.company.id
            domain = [('company_id', '=', company_id), ('type', '=', journal_type)]
            if m.move_type in ['in_refund','out_refund']:
                domain.append(('show_in_credit_note', '=', True))
            m.suitable_journal_ids = self.env['account.journal'].search(domain)
        return res





class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_m = fields.Boolean(string='M',compute='_compute_is_g_or_m',store=True,readonly=False)
    is_g = fields.Boolean(string='G',compute='_compute_is_g_or_m',store=True,readonly=False)


    @api.depends('journal_id')
    def _compute_is_g_or_m(self):
        for rec in self:
            rec.is_m = rec.journal_id.is_m
            rec.is_g = rec.journal_id.is_g