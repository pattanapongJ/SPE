# -*- coding: utf-8 -*-
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payment_vals_from_wizard(self):
        move_ids = self.line_ids.mapped('move_id')
        payment_vals = super()._create_payment_vals_from_wizard()
        if move_ids:
            for move in move_ids.sorted(key=lambda m: m.invoice_date):
                invoice_user_employee_id = move.invoice_user_employee_id.id
                sale_spec_employee = move.sale_spec_employee.id
                sale_manager_employee_id = move.sale_manager_employee_id.id
                user_sale_agreement_employee = move.user_sale_agreement_employee.id
                department_id = move.department_id.id

            if invoice_user_employee_id:
                payment_vals['invoice_user_employee_id'] = invoice_user_employee_id
            if sale_spec_employee:
                payment_vals['sale_spec_employee'] = sale_spec_employee
            if sale_manager_employee_id:
                payment_vals['sale_manager_employee_id'] = sale_manager_employee_id
            if user_sale_agreement_employee:
                payment_vals['user_sale_agreement_employee'] = user_sale_agreement_employee
            if department_id:
                payment_vals['department_id'] = department_id

        return payment_vals