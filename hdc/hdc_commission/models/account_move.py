# -*- coding: utf-8 -*-
from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_settle_commission_salesperson = fields.Boolean(string ="Is settle commission Salesperson")
    is_settle_commission_sale_spec = fields.Boolean(string ="Is settle commission Sale Spec")
    is_settle_commission_sale_manager = fields.Boolean(string ="Is settle commission Sale Manager")
    is_settle_commission_mall = fields.Boolean(string ="Is settle commission Mall")
    is_settle_commission_mall_salesperson = fields.Boolean(string ="Is settle commission Mall Salesperson")
    is_settle_commission_mall_sale_spec = fields.Boolean(string ="Is settle commission Mall Sale Spec")
    is_settle_commission_mall_sale_manager = fields.Boolean(string ="Is settle commission Mall Sale Manager")

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    commission_code = fields.Many2many('commission.type', string = 'Commission Code',)
    commission_remarks = fields.Char(string='Commission Remarks')