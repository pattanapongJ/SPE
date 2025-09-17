from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'bs.base.finance.dimension']

    def _check_required_dimensions(self):
        for rec in self.filtered(lambda x: x.state == 'draft'):
            for line in rec.invoice_line_ids.filtered(lambda x: not x.display_type):
                _dimension1 = self.env.ref('bs_finance_dimension.bs_dimension_1', raise_if_not_found=False)
                _dimension2 = self.env.ref('bs_finance_dimension.bs_dimension_2', raise_if_not_found=False)
                _dimension3 = self.env.ref('bs_finance_dimension.bs_dimension_3', raise_if_not_found=False)
                if line.need_finance_dimension_1:
                    raise ValidationError(_('%s is required.', _dimension1.name if _dimension1 else 'Dimension 1'))
                if line.need_finance_dimension_2:
                    raise ValidationError(_('%s is required.', _dimension2.name if _dimension2 else 'Dimension 2'))
                if line.need_finance_dimension_3:
                    raise ValidationError(_('%s is required.', _dimension3.name if _dimension3 else 'Dimension 3'))

    def action_post(self):
        self._check_required_dimensions()
        return super(AccountMove, self).action_post()


class AccountMoveLine(models.Model):
    _name = 'account.move.line'
    _inherit = ['account.move.line', 'bs.base.finance.dimension']


    @api.model
    def default_get(self, fields):
        rec = super().default_get(fields)
        if self.move_id:
            self.update({
            'finance_dimension_1_id': self.finance_dimension_1_id or self.move_id.finance_dimension_1_id.id,
            'finance_dimension_2_id': self.finance_dimension_2_id or self.move_id.finance_dimension_2_id.id,
            'finance_dimension_3_id': self.finance_dimension_3_id or self.move_id.finance_dimension_3_id.id
        })

        return rec


    need_finance_dimension_1 = fields.Boolean(string=_('Need Dimension 1'), compute='_compute_required_dimension')
    need_finance_dimension_2 = fields.Boolean(string=_('Need Dimension 2'), compute='_compute_required_dimension')
    need_finance_dimension_3 = fields.Boolean(string=_('Need Dimension 3'), compute='_compute_required_dimension')

    @api.depends('move_id', 'account_id','finance_dimension_1_id','finance_dimension_2_id','finance_dimension_3_id')
    def _compute_required_dimension(self):
        for rec in self:
            rec.need_finance_dimension_1 = rec.account_id.need_finance_dimension_1 and rec.parent_state == 'draft' and not rec.finance_dimension_1_id
            rec.need_finance_dimension_2 = rec.account_id.need_finance_dimension_2 and rec.parent_state == 'draft' and not rec.finance_dimension_2_id
            rec.need_finance_dimension_3 = rec.account_id.need_finance_dimension_3 and rec.parent_state == 'draft' and not rec.finance_dimension_3_id
