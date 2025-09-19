# Copyright 2013 Guewen Baconnier, Camptocamp SA
# Copyright 2022 Aritz Olea, Landoo SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
import re

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"

    term_of_delivery_id = fields.Many2one(comodel_name="account.incoterms", string="Term Of Delivery")

    @api.onchange('fiscal_position_id')
    def _onchange_fiscal_position_id(self):
        for line in self.order_line:
            fpos = self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(self.partner_id.id)
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda t: t.company_id == line.env.company)
            line.tax_id = fpos.map_tax(taxes, line.product_id, self.partner_shipping_id)

    @api.onchange('user_id')
    def onchange_user_id(self):
        print("onchange_user_id called in SaleOrder")
        pass

    @api.onchange('partner_id')
    def onchange_partner_id_team_id(self):
        values = { }
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        user_id = partner_user.id
        # if not self.env.context.get('not_self_saleperson') or not self.team_id:
        #     values['team_id'] = self.env['crm.team'].with_context(
        #         default_team_id=self.partner_id.team_id.id
        #     )._get_default_team_id(domain=['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)], user_id=user_id)
        # if self.partner_id.team_id:
        #     values['team_id'] = self.partner_id.team_id
        self.update(values)

    @api.onchange('partner_id')
    def onchange_partner_id_team_id_credit_limit(self):
        customer_credit_id = self.env["customer.credit.limit"].search([('partner_id', '=', self.partner_id.id)])
        if customer_credit_id.credit_id.credit_line:
            credit_line = customer_credit_id.credit_id.credit_line
            if len(credit_line) > 0:
                self.team_id = credit_line[0].sale_team_id
                self.user_id = credit_line[0].sale_user_id

        if self.partner_id.credit_limit_on_hold == True:
            return {
                    'warning': {'title': "Customer On Hold", 
                                'message': 
                                "Customer have been on hold. Please contact administration for further guidance"
                                },
                }
        
        if customer_credit_id:
            credit_team_remain = 0
            sale_team_id = False
            if customer_credit_id:
                sale_team_id = customer_credit_id.credit_id.credit_line.filtered(lambda l: l.sale_team_id == self.team_id)
                if sale_team_id:
                    credit_team_remain = sale_team_id.credit_remain

            if customer_credit_id.cash_remain <= 0 or credit_team_remain <= 0:
                partner_id = self.partner_id

                exceeded_amount_team = credit_team_remain - self.amount_total
                exceeded_amount_team = "{:.2f}".format(exceeded_amount_team)
                exceeded_amount_team = float(exceeded_amount_team)
                
                return {
                    'warning': {'title': "Credit Limit Warning", 
                                'message': 
                                "Customer: %s \nCredit Remain: %.2f  \nCash Limit: %.2f \nExceeded Amount (Credit): %.2f "  
                                % (partner_id.name, credit_team_remain ,partner_id.cash_limit ,exceeded_amount_team),
                                },
                }
        
    
    def action_view_invoice(self):
        res = super(SaleOrder,self).action_view_invoice()
        invoices = self.mapped('invoice_ids')
        if invoices:
            for invoice in invoices:
                if not invoice.form_no:
                    invoice._onchange_journal_default_prefix()
        return res
    
    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        finance_dimension_2_id = self.env['bs.finance.dimension'].search([
                ('res_id', '=', self.user_id.id)
            ], limit=1)

        if finance_dimension_2_id:
            res["finance_dimension_2_id"] = finance_dimension_2_id.id
        res['modify_type_txt'] = self.modify_type_txt if self.modify_type_txt else False
        res['plan_home'] = self.plan_home if self.plan_home else False
        res['project_name'] = self.project_name.id if self.project_name else False
        res['customer_po'] = self.customer_po if self.customer_po else False
        res['room'] = self.room if self.room else False

        return res
    
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    modify_type_txt = fields.Char(string="แปลง/Type/Block", related="order_id.modify_type_txt") 
    plan_home = fields.Char(string="แบบบ้าน", related="order_id.plan_home")
    room = fields.Char(string="ชั้น/ห้อง", related="order_id.room")

    external_product_id = fields.Many2one('multi.external.product',string="External Product")
    external_customer = fields.Many2one('res.partner', string="External Customer",store=True)
    external_item = fields.Char(string="External Item",store=True)
    barcode_customer = fields.Char(string="Barcode Customer",store=True)
    barcode_modern_trade = fields.Char(string="Barcode Product",store=True)
    description_customer = fields.Text(string="External Description",store=True)

    tags_product_sale_ids = fields.Many2many(related='product_id.tags_product_sale_ids', string='Tags')


    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res['modify_type_txt'] = self.modify_type_txt if self.modify_type_txt else False
        res['plan_home'] = self.plan_home if self.plan_home else False
        res['room'] = self.room if self.room else False
        res['external_customer'] = self.external_customer.id if self.external_customer else False
        res['external_item'] = self.external_item if self.external_item else False
        res['barcode_customer'] = self.barcode_customer if self.barcode_customer else False
        res['barcode_modern_trade'] = self.barcode_modern_trade if self.barcode_modern_trade else False
        res['description_customer'] = self.description_customer if self.description_customer else False
        return res

    @api.onchange('product_id', 'product_template_id', 'order_id.partner_id', 'product_uom')
    def _onchange_external_product(self):
        if self.product_template_id and self.order_id.partner_id:
            # ค้นหาข้อมูลจาก partner_id ก่อน
            external_product = self.env['multi.external.product'].search([
                ('product_tmpl_id', '=', self.product_template_id.id),
                ('partner_id', '=', self.order_id.partner_id.id),
                # ('uom_id', '=', self.product_id.uom_id.id)
            ], limit=1)

            if not external_product:
                external_product = self.env['multi.external.product'].search([
                    ('product_tmpl_id', '=', self.product_template_id.id),
                    ('company_chain_id', '=', self.order_id.partner_id.company_chain_id.id),
                    # ('uom_id', '=', self.product_id.uom_id.id)
                ], limit=1)

            self.external_product_id = external_product.id if external_product else False
            if self.external_product_id:
                barcode_modern_trade_ids = self.external_product_id.barcode_spe_ids.filtered(lambda x: x.uom_id == self.product_uom)
                print("barcode_modern_trade_ids-", barcode_modern_trade_ids)
                if barcode_modern_trade_ids:
                    barcode_modern_trade = barcode_modern_trade_ids[0].barcode_modern_trade
                else:
                    barcode_modern_trade = False
                self.external_item = self.external_product_id.name
                self.barcode_customer = self.external_product_id.barcode_modern_trade
                self.barcode_modern_trade = barcode_modern_trade
                self.description_customer = self.external_product_id.product_description
            else:
                self.external_item = False
                self.barcode_customer = False
                self.barcode_modern_trade = False
                self.description_customer = False

# class SaleOrderTypology(models.Model):
#    _inherit = "sale.order.type"

#    inter_company_transactions = fields.Boolean(string='Inter Company Transactions')
