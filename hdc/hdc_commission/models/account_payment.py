from odoo import models, fields

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_settle_commission_salesperson = fields.Boolean(string ="Is settle commission Salesperson")
    is_settle_commission_sale_spec = fields.Boolean(string ="Is settle commission Sale Spec")
    is_settle_commission_sale_manager = fields.Boolean(string ="Is settle commission Sale Manager")
    is_settle_commission_mall = fields.Boolean(string ="Is settle commission Mall")
    is_settle_commission_mall_salesperson = fields.Boolean(string ="Is settle commission Mall Salesperson")
    is_settle_commission_mall_sale_spec = fields.Boolean(string ="Is settle commission Mall Sale Spec")
    is_settle_commission_mall_sale_manager = fields.Boolean(string ="Is settle commission Mall Sale Manager")

    no_commission = fields.Boolean(string = "No Commssion",tracking=True)
    commission_remark = fields.Text('Commission Remark',tracking=True)