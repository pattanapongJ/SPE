from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountPaymentDeduction(models.TransientModel):
    _name = "account.payment.deduction"
    _inherit = ['account.payment.deduction', 'bs.base.finance.dimension']

    need_finance_dimension_1 = fields.Boolean(string=_('Need Dimension 1'), compute='_compute_required_dimension')
    need_finance_dimension_2 = fields.Boolean(string=_('Need Dimension 2'), compute='_compute_required_dimension')
    need_finance_dimension_3 = fields.Boolean(string=_('Need Dimension 3'), compute='_compute_required_dimension')

    @api.depends('account_id')
    def _compute_required_dimension(self):
        for rec in self:
            rec.need_finance_dimension_1 = rec.account_id.need_finance_dimension_1 and not rec.finance_dimension_1_id
            rec.need_finance_dimension_2 = rec.account_id.need_finance_dimension_2 and not rec.finance_dimension_2_id
            rec.need_finance_dimension_3 = rec.account_id.need_finance_dimension_3 and not rec.finance_dimension_3_id

    def _check_required_dimensions(self):
        for line in self:
            _dimension1 = self.env.ref('bs_finance_dimension.bs_dimension_1', raise_if_not_found=False)
            _dimension2 = self.env.ref('bs_finance_dimension.bs_dimension_2', raise_if_not_found=False)
            _dimension3 = self.env.ref('bs_finance_dimension.bs_dimension_3', raise_if_not_found=False)
            if line.need_finance_dimension_1:
                raise ValidationError(_('%s is required.', _dimension1.name if _dimension1 else 'Dimension 1'))
            if line.need_finance_dimension_2:
                raise ValidationError(_('%s is required.', _dimension2.name if _dimension2 else 'Dimension 2'))
            if line.need_finance_dimension_3:
                raise ValidationError(_('%s is required.', _dimension3.name if _dimension3 else 'Dimension 3'))

    def _finance_dimension_values(self):
        return {
            'finance_dimension_1_id': self.finance_dimension_1_id.id,
            'finance_dimension_2_id': self.finance_dimension_2_id.id,
            'finance_dimension_3_id': self.finance_dimension_3_id.id
        }


class AccountPaymentRegister(models.TransientModel):
    _name = 'account.payment.register'
    _inherit = ["account.payment.register", "bs.base.finance.dimension"]

    def _prepare_deduct_move_line(self, deduct):
        deduct._check_required_dimensions()
        _value = super(AccountPaymentRegister, self)._prepare_deduct_move_line(deduct)
        _value['deduct_id'] = deduct
        _value.update(deduct._finance_dimension_values())
        return _value

    def _create_payments(self):
        _finance_context = self.finance_context()
        if self.payment_difference_handling == "reconcile_multi_deduct":
            _finance_context.update({
                "skip_account_move_synchronization": True,
                "dont_redirect_to_payments": True,
            })
        payment = super(AccountPaymentRegister,
                        self.with_context(_finance_context))._create_payments()
        tax_invoice = payment.tax_invoice_ids.mapped("move_id")
        if tax_invoice:
            tax_invoice.line_ids.write(self._finance_dimension_values())
        return payment

    def _finance_dimension_values(self):
        return {
            'finance_dimension_1_id': self.finance_dimension_1_id.id,
            'finance_dimension_2_id': self.finance_dimension_2_id.id,
            'finance_dimension_3_id': self.finance_dimension_3_id.id
        }

    def finance_context(self):
        return {
            'from_payment': True,
            'finance_dimension_1_id': self.finance_dimension_1_id.id,
            'finance_dimension_2_id': self.finance_dimension_2_id.id,
            'finance_dimension_3_id': self.finance_dimension_3_id.id
        }

    @api.model
    def _get_deduction_ids_context(self, existing_context):
        context = super(AccountPaymentRegister, self)._get_deduction_ids_context(existing_context)
        context.update({
            'default_finance_dimension_1_id':  'finance_dimension_1_id',
            'default_finance_dimension_2_id':  'finance_dimension_2_id',
            'default_finance_dimension_3_id':  'finance_dimension_3_id'
        })
        return context
