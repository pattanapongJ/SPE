# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, tools, api

_logger = logging.getLogger(__name__)

class AccountMovePartialReconcile(models.Model):
    _name = 'move.partial.reconcile.info'
    _auto = False
    _description = 'Account Move Partial Reconcile'

    id = fields.Integer(readonly=True)
    partial_reconcile_id = fields.Many2one(
        'account.partial.reconcile',
        string='Partial Reconcile',
        readonly=True
    )
    reconciled_line_id = fields.Many2one(
        'account.move.line',
        string='Reconciled Line',
        readonly=True
    )
    move_id = fields.Many2one(
        'account.move',
        string='Account Move',
        readonly=True
    )
    invoice_date = fields.Date(
        string='Invoice/Bill Date',
        readonly=True
    )
    move_name = fields.Char(
        string='Number',
        readonly=True
    )
    reference = fields.Char(
        string='Reference',
        readonly=True
    )
    reconcile_date = fields.Date(
        string='Reconcile Date',
        readonly=True
    )
    amount = fields.Float(
        string='Total',
        readonly=True
    )
    status = fields.Selection(
        related='reconciled_line_id.move_id.state',
        string='Status',
        readonly=True
    )

    @api.model
    def _select(self):
        return """
            SELECT
                apr.debit_move_id AS id,
                apr.id AS partial_reconcile_id,
                apr.debit_move_id AS reconciled_line_id,
                aml_credit.move_id AS move_id,
                aml_debit.date AS invoice_date,
                aml_debit.move_name AS move_name,
                aml_debit.ref AS reference,
                apr.reconcile_date AS reconcile_date,
                apr.amount AS amount
            FROM
                account_partial_reconcile apr
            JOIN
                account_move_line aml_debit ON apr.debit_move_id = aml_debit.id
            JOIN
                account_move_line aml_credit ON apr.credit_move_id = aml_credit.id
            
            UNION ALL
            
            SELECT
                apr.credit_move_id AS id,
                apr.id AS partial_reconcile_id,
                apr.credit_move_id AS reconciled_line_id,
                aml_debit.move_id AS move_id,
                aml_credit.date AS invoice_date,
                aml_credit.move_name AS move_name,
                aml_credit.ref AS reference,
                apr.reconcile_date AS reconcile_date,
                apr.amount AS amount
            FROM
                account_partial_reconcile apr
            JOIN
                account_move_line aml_credit ON apr.credit_move_id = aml_credit.id
            JOIN
                account_move_line aml_debit ON apr.debit_move_id = aml_debit.id

        """

    def init(self):
        tools.drop_view_if_exists(self._cr, 'move_partial_reconcile_info')
        self._cr.execute("""CREATE OR REPLACE VIEW move_partial_reconcile_info AS (%s)""" % (self._select()))


