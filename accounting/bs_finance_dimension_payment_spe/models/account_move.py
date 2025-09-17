# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_finance_dimension_values(self):
        return {
            "finance_dimension_1_id": self.finance_dimension_1_id.id,
            "finance_dimension_2_id": self.finance_dimension_2_id.id,
            "finance_dimension_3_id": self.finance_dimension_3_id.id,
            "finance_dimension_4_id": self.finance_dimension_4_id.id,
            "finance_dimension_5_id": self.finance_dimension_5_id.id,
            "finance_dimension_6_id": self.finance_dimension_6_id.id,
            "finance_dimension_7_id": self.finance_dimension_7_id.id,
            "finance_dimension_8_id": self.finance_dimension_8_id.id,
            "finance_dimension_9_id": self.finance_dimension_9_id.id,
            "finance_dimension_10_id": self.finance_dimension_10_id.id,
        }


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _create_exchange_difference_move(self):
        exchange_move = super(AccountMoveLine, self)._create_exchange_difference_move()
        if exchange_move and self._context.get("from_payment", False):
            exchange_move.line_ids.write(
                {
                    "finance_dimension_4_id": self._context.get(
                        "finance_dimension_4_id"
                    ),
                    "finance_dimension_5_id": self._context.get(
                        "finance_dimension_5_id"
                    ),
                    "finance_dimension_6_id": self._context.get(
                        "finance_dimension_6_id"
                    ),
                    "finance_dimension_7_id": self._context.get(
                        "finance_dimension_7_id"
                    ),
                    "finance_dimension_8_id": self._context.get(
                        "finance_dimension_8_id"
                    ),
                    "finance_dimension_9_id": self._context.get(
                        "finance_dimension_9_id"
                    ),
                    "finance_dimension_10_id": self._context.get(
                        "finance_dimension_10_id"
                    ),
                }
            )
        return exchange_move

    def _check_dimenstion_update(self, vals):
        result = super(AccountMoveLine, self)._check_dimenstion_update(vals)
        return (
                result
                or "finance_dimension_4_id" in vals
                or "finance_dimension_5_id" in vals
                or "finance_dimension_6_id" in vals
                or "finance_dimension_7_id" in vals
                or "finance_dimension_8_id" in vals
                or "finance_dimension_9_id" in vals
                or "finance_dimension_10_id" in vals
        )
