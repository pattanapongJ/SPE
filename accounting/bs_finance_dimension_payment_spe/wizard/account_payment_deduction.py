# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountPaymentDeduction(models.TransientModel):
    _inherit = "account.payment.deduction"

    need_finance_dimension_4 = fields.Boolean(
        string=_("Need Dimension 4"), compute="_compute_required_dimension"
    )
    need_finance_dimension_5 = fields.Boolean(
        string=_("Need Dimension 5"), compute="_compute_required_dimension"
    )
    need_finance_dimension_6 = fields.Boolean(
        string=_("Need Dimension 6"), compute="_compute_required_dimension"
    )
    need_finance_dimension_7 = fields.Boolean(
        string=_("Need Dimension 7"), compute="_compute_required_dimension"
    )
    need_finance_dimension_8 = fields.Boolean(
        string=_("Need Dimension 8"), compute="_compute_required_dimension"
    )
    need_finance_dimension_9 = fields.Boolean(
        string=_("Need Dimension 9"), compute="_compute_required_dimension"
    )
    need_finance_dimension_10 = fields.Boolean(
        string=_("Need Dimension 10"), compute="_compute_required_dimension"
    )

    @api.depends("account_id")
    def _compute_required_dimension(self):
        super(AccountPaymentDeduction, self)._compute_required_dimension()
        for rec in self:
            rec.need_finance_dimension_4 = (
                    rec.account_id.need_finance_dimension_4
                    and not rec.finance_dimension_4_id
            )
            rec.need_finance_dimension_5 = (
                    rec.account_id.need_finance_dimension_5
                    and not rec.finance_dimension_5_id
            )
            rec.need_finance_dimension_6 = (
                    rec.account_id.need_finance_dimension_6
                    and not rec.finance_dimension_6_id
            )
            rec.need_finance_dimension_7 = (
                    rec.account_id.need_finance_dimension_7
                    and not rec.finance_dimension_7_id
            )
            rec.need_finance_dimension_8 = (
                    rec.account_id.need_finance_dimension_8
                    and not rec.finance_dimension_8_id
            )
            rec.need_finance_dimension_9 = (
                    rec.account_id.need_finance_dimension_9
                    and not rec.finance_dimension_9_id
            )
            rec.need_finance_dimension_10 = (
                    rec.account_id.need_finance_dimension_10
                    and not rec.finance_dimension_10_id
            )

    def _check_required_dimensions(self):
        super(AccountPaymentDeduction, self)._check_required_dimensions()
        for line in self:
            _dimension4 = self.env.ref(
                "bs_finance_dimension_spe.bs_dimension_4", raise_if_not_found=False
            )
            _dimension5 = self.env.ref(
                "bs_finance_dimension_spe.bs_dimension_5", raise_if_not_found=False
            )
            _dimension6 = self.env.ref(
                "bs_finance_dimension_spe.bs_dimension_6", raise_if_not_found=False
            )
            _dimension7 = self.env.ref(
                "bs_finance_dimension_spe.bs_dimension_7", raise_if_not_found=False
            )
            _dimension8 = self.env.ref(
                "bs_finance_dimension_spe.bs_dimension_8", raise_if_not_found=False
            )
            _dimension9 = self.env.ref(
                "bs_finance_dimension_spe.bs_dimension_9", raise_if_not_found=False
            )
            _dimension10 = self.env.ref(
                "bs_finance_dimension_spe.bs_dimension_10", raise_if_not_found=False
            )

            if line.need_finance_dimension_4:
                raise ValidationError(
                    _(
                        "%s is required.",
                        _dimension4.name if _dimension4 else "Dimension 4",
                    )
                )
            if line.need_finance_dimension_5:
                raise ValidationError(
                    _(
                        "%s is required.",
                        _dimension5.name if _dimension5 else "Dimension 5",
                    )
                )
            if line.need_finance_dimension_6:
                raise ValidationError(
                    _(
                        "%s is required.",
                        _dimension6.name if _dimension6 else "Dimension 6",
                    )
                )
            if line.need_finance_dimension_7:
                raise ValidationError(
                    _(
                        "%s is required.",
                        _dimension7.name if _dimension7 else "Dimension 7",
                    )
                )
            if line.need_finance_dimension_8:
                raise ValidationError(
                    _(
                        "%s is required.",
                        _dimension8.name if _dimension8 else "Dimension 8",
                    )
                )
            if line.need_finance_dimension_9:
                raise ValidationError(
                    _(
                        "%s is required.",
                        _dimension9.name if _dimension9 else "Dimension 9",
                    )
                )
            if line.need_finance_dimension_10:
                raise ValidationError(
                    _(
                        "%s is required.",
                        _dimension10.name if _dimension10 else "Dimension 10",
                    )
                )

    def _finance_dimension_values(self):
        vals = super(AccountPaymentDeduction, self)._finance_dimension_values()
        vals.update(
            {
                "finance_dimension_4_id": self.finance_dimension_4_id.id,
                "finance_dimension_5_id": self.finance_dimension_5_id.id,
                "finance_dimension_6_id": self.finance_dimension_6_id.id,
                "finance_dimension_7_id": self.finance_dimension_7_id.id,
                "finance_dimension_8_id": self.finance_dimension_8_id.id,
                "finance_dimension_9_id": self.finance_dimension_9_id.id,
                "finance_dimension_10_id": self.finance_dimension_10_id.id,
            }
        )

        return vals


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    @api.model
    def default_get(self, fields_list):
        # OVERRIDE
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        if active_model in ["account.move.line", "account.move"]:
            active_ids = self.env.context.get("active_ids", [])
            move_ids = self.env["account.move"]
            if active_model == "account.move":
                move_ids = self.env["account.move"].browse(active_ids)
            elif active_model == "account.move.line":
                move_lines = self.env["account.move.line"].browse(active_ids)
                move_ids = move_lines.mapped("move_id")
            dimension_vals = (
                move_ids[0]._get_finance_dimension_values() if move_ids else {}
            )
            res.update(dimension_vals)

        return res

    def _finance_dimension_values(self):
        vals = super(AccountPaymentRegister, self)._finance_dimension_values()
        vals.update(
            {
                "finance_dimension_4_id": self.finance_dimension_4_id.id,
                "finance_dimension_5_id": self.finance_dimension_5_id.id,
                "finance_dimension_6_id": self.finance_dimension_6_id.id,
                "finance_dimension_7_id": self.finance_dimension_7_id.id,
                "finance_dimension_8_id": self.finance_dimension_8_id.id,
                "finance_dimension_9_id": self.finance_dimension_9_id.id,
                "finance_dimension_10_id": self.finance_dimension_10_id.id,
            }
        )

        return vals

    def finance_context(self):
        vals = super(AccountPaymentRegister, self).finance_context()
        vals.update(
            {
                "finance_dimension_4_id": self.finance_dimension_4_id.id,
                "finance_dimension_5_id": self.finance_dimension_5_id.id,
                "finance_dimension_6_id": self.finance_dimension_6_id.id,
                "finance_dimension_7_id": self.finance_dimension_7_id.id,
                "finance_dimension_8_id": self.finance_dimension_8_id.id,
                "finance_dimension_9_id": self.finance_dimension_9_id.id,
                "finance_dimension_10_id": self.finance_dimension_10_id.id,
            }
        )

        return vals

    @api.model
    def _get_deduction_ids_context(self, existing_context):
        context = super(AccountPaymentRegister, self)._get_deduction_ids_context(
            existing_context
        )
        context.update(
            {
                "default_finance_dimension_4_id": "finance_dimension_4_id",
                "default_finance_dimension_5_id": "finance_dimension_5_id",
                "default_finance_dimension_6_id": "finance_dimension_6_id",
                "default_finance_dimension_7_id": "finance_dimension_7_id",
                "default_finance_dimension_8_id": "finance_dimension_8_id",
                "default_finance_dimension_9_id": "finance_dimension_9_id",
                "default_finance_dimension_10_id": "finance_dimension_10_id",
            }
        )
        return context
