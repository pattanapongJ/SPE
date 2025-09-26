# -*- coding: utf-8 -*-
from lxml import etree
from odoo import api, models, fields, _
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError

class SaleOrderTypology(models.Model):
    _inherit = "sale.order.type"

    is_credit_limit = fields.Boolean("Check Credit Limit")

    below_cost = fields.Boolean("Approve Below Cost", default=False)
    pass_credit_limit = fields.Boolean("Pass Credit Limit")

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    note = fields.Text('Note')

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_ref = fields.Char(related='partner_id.ref')
    user_employee_id = fields.Many2one('hr.employee', string = 'Salesperson', index = True)
    temp_credit_count = fields.Integer(compute="_compute_temp_credit_count")
    temp_credit_ids = fields.Many2many('temp.credit.request', string="Temp Credit Request", compute="_compute_temp_credit_count")
    temp_credit_create = fields.Integer(compute="_compute_temp_credit_create")
    check_credit_approve = fields.Boolean("Check Credit Approved",
                                          compute="_compute_check_credit_approve", index=True)
    payment_method_id = fields.Many2one('account.payment.method', string ='Payment Method')
    approve_credit_amount = fields.Float('Approve Credit Amount', digits='Product Price', default=0.0,copy=False)
    old_total_price = fields.Float('Old Total Price', digits='Product Price', default=0.0,copy=False)
    so_invoice_amount = fields.Float(string="SO Invoice Amount", compute='_compute_so_invoice_amount',store=False)
    check_credit_exceed = fields.Boolean('Check Credit Exceed',compute="_compute_check_credit_exceed", index=True)
    check_cash_exceed = fields.Boolean('Check Cash Exceed',compute="_compute_check_credit_exceed", index=True)

    is_credit_limit = fields.Boolean(related='type_id.is_credit_limit',string="Check Credit Limit")
    remark_onhold = fields.Text('Remark On Hold')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        - Sales Team
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False, 'partner_shipping_id': False, 'fiscal_position_id': False,
                })
            return

        self = self.with_company(self.company_id)

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        values = {
            # 'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'partner_invoice_id': addr['invoice'], 'partner_shipping_id': addr['delivery'],
            }
        user_id = partner_user.id
        if not self.env.context.get('not_self_saleperson'):
            user_id = user_id or self.env.context.get('default_user_id', self.env.uid)
        if user_id and self.user_id.id != user_id:
            values['user_id'] = user_id

        if self.env['ir.config_parameter'].sudo().get_param(
                'account.use_invoice_terms') and self.env.company.invoice_terms:
            values['note'] = self.with_context(lang = self.partner_id.lang).env.company.invoice_terms
        # if not self.env.context.get('not_self_saleperson') or not self.team_id:
        #     values['team_id'] = self.env['crm.team'].with_context(
        #         default_team_id = self.partner_id.team_id.id)._get_default_team_id(
        #         domain = ['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)], user_id = user_id)
        self.update(values)



    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        if self.temp_credit_create > 0:
            credit_request = self.env['temp.credit.request'].search([('order_no', '=', self.id)])
            credit_request.action_cancel()
        return res

    def _compute_check_credit_approve(self):
        for rec in self:
            credit_request = self.env['temp.credit.request'].search([('order_no', '=', rec.id),('state', '!=', "cancel")])
            check_credit_approve = False
            for order in credit_request:
                if order.state == "approved":
                    rec.check_credit_approve = True
                    return
            rec.check_credit_approve = check_credit_approve
    def _compute_temp_credit_create(self):
        for rec in self:
            credit_request = self.env['temp.credit.request'].search([('order_no', '=', rec.id),('state', '!=', "cancel")])
            rec.temp_credit_create = len(credit_request)

    def _compute_temp_credit_count(self):
        for rec in self:
            credit_request = self.env['temp.credit.request'].search([('order_no', '=', rec.id)])
            rec.temp_credit_ids = credit_request.ids
            rec.temp_credit_count = len(credit_request)

    def create_credit_request(self):
        action = {
            'name': _('Temp Credit Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'temp.credit.request',
            "views": [(self.env.ref("hdc_creditlimit_saleteam.view_temp_credit_request_form").id, "form")],
            'view_mode': 'form',
            'context': {
                'default_order_no': self.id,
                'default_partner_id': self.partner_id.id,
                'default_sale_person': self.user_id.id,
                'default_sale_team_id': self.team_id.id,
                },
            }
        return action

    def action_temp_credit(self):
        action = {'name': "Temp Credit Request",
                'view_mode': 'tree,form',
                'view_id': False,
                'res_model': 'temp.credit.request',
                'type': 'ir.actions.act_window',
                'domain': [('order_no', '=', self.id)],
                }
        return action
    
    # @api.onchange('payment_term_id')
    # def _onchange_payment_term_id(self):
    #     if self.partner_id.credit_type == 'new' and self.payment_term_id.is_cash is False:
    #         raise UserError(_("ไม่อนุญาตให้ทำการขาย เนื่องจากเงื่อนไขการชำระเงินไม่ถูกต้อง"))

    def show_below_cost_warning_wizard(self, list_warning_below_cost=[]):

        messages = []

        for list in list_warning_below_cost:

            line_message = f"{list['product']}, price: {list['price']}, cost: {list['cost']}"
            messages.append(line_message)

        message = "Your order has found selling price below cost. \n" + "\n".join(
            messages
        )

        return {
            "name": _("Below Cost Warning Sale Order"),
            "type": "ir.actions.act_window",
            "res_model": "below.cost.warning.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_sale_order_id": self.id,
                "default_message": message,
            },
        }
        
    def action_sale_ok(self):
        self.old_total_price = self.amount_total
        list_warning_below_cost = []

        order_currency   = self.currency_id               # สกุลเงินของ SO
        company_currency = self.company_id.currency_id    # สกุลเงินบริษัท
        conv_date        = self.date_order or fields.Date.context_today(self)

        for line in self.order_line:
            # ข้าม service
            if line.product_id.product_tmpl_id.type == "service":
                continue

            fixed_price_order_cur = line.price_unit

            in_pricelist = self.env['product.pricelist.item'].search([
                ('pricelist_id', '=', self.pricelist_id.id),
                ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
            ], limit=1)

            if in_pricelist and in_pricelist.pricelist_cost_price:
                cost_company_cur = in_pricelist.pricelist_cost_price
            else:
                cost_company_cur = line.product_id.product_tmpl_id.standard_price or 0.0

            cost_price_order_cur = cost_company_cur
            if self.type_id.is_oversea:
                if self.currency_id.name != "THB":
                    cost_price_order_cur = company_currency._convert(
                        cost_company_cur, order_currency, self.company_id, conv_date
                    )

            if (not self.pricelist_id.approve_below_cost
                and not self.type_id.below_cost
                and not line.product_id.product_tmpl_id.below_cost):
                if cost_price_order_cur > fixed_price_order_cur:
                    list_warning_below_cost.append({
                        'product': line.product_id.name,
                        'price': fixed_price_order_cur,
                        'cost' : cost_price_order_cur,
                    })

        if list_warning_below_cost and not self.is_confirm_below_cost:
            return self.show_below_cost_warning_wizard(list_warning_below_cost)


        # ------------------------------------------

        if self.type_id.is_credit_limit == True:
            partner_id = self.partner_id
            customer_credit_id = self.env["customer.credit.limit"].search([('partner_id', '=', self.partner_id.id)])
            sale_team_not_match = False
            if customer_credit_id:
                sale_team_id = customer_credit_id.credit_id.credit_line.filtered(lambda l: l.sale_team_id == self.team_id)
                if not sale_team_id:
                    sale_team_not_match = True
            
            if (partner_id.credit_type == 'new' or sale_team_not_match) and self.payment_term_id.is_cash is False:
                raise UserError(_("ไม่อนุญาตให้ทำการขาย เนื่องจากเงื่อนไขการชำระเงินไม่ถูกต้อง"))
            if self.partner_id.parent_id:
                partner_id = self.partner_id.parent_id
            partner_ids = [partner_id.id]
            for partner in partner_id.child_ids:
                partner_ids.append(partner.id)
            # Total Credit Receivable (Post Invoice)
            credit = 0
            account_id = self.env['account.move'].search([  ('partner_id', 'in', partner_ids),('is_cash', '=', False),
                                                            ('state', '=', 'posted'), ('move_type', '=', 'out_invoice')])

            invoiced_amount = 0
            payment_amount = 0
            for acc in account_id:
                invoiced_amount += acc.amount_residual
            account_entry_id = self.env['account.move'].search(
                [('partner_id', 'in', partner_ids), ('state', '=', 'posted'), ('move_type', '=', 'entry')])

            account_payment = self.env['account.payment'].search(
                [('move_id', 'in', account_entry_id.ids),('is_cheque', '=', True)])
            account_payment_done = self.env['account.payment'].search(
                [('move_id', 'in', account_entry_id.ids),('pdc_id.state', '=', 'done'),('is_cheque', '=', True)])
            for payment in account_payment:
                payment_amount += payment.amount
            for payment_done in account_payment_done:
                payment_amount -= payment_done.pdc_id.payment_amount

            invoiced_amount = invoiced_amount + payment_amount
            credit = invoiced_amount

            # Total Cash Receivable (Post Invoice)
            account_id_cash = self.env['account.move'].search([  ('partner_id', 'in', partner_ids),('is_cash', '=', True),
                                                            ('state', '=', 'posted'), ('move_type', '=', 'out_invoice')])
            invoiced_amount_cash = 0
            for acc_cash in account_id_cash:
                invoiced_amount_cash += acc_cash.amount_residual
            cash = invoiced_amount_cash

            # Total Credit Receivable (Post Invoice) Sale Team
            credit_team = 0
            account_id_team = self.env['account.move'].search([ ('team_id', '=', self.team_id.id),
                                                                ('partner_id', 'in', partner_ids),('is_cash', '=', False),
                                                                ('state', '=', 'posted'), ('move_type', '=', 'out_invoice')])

            invoiced_amount_team = 0
            payment_amount_team = 0
            for acc_team in account_id_team:
                invoiced_amount_team += acc_team.amount_residual
            account_entry_id_team = self.env['account.move'].search(
                [('partner_id', 'in', partner_ids), ('state', '=', 'posted'), ('move_type', '=', 'entry')])

            account_payment_team = self.env['account.payment'].search(
                [('move_id', 'in', account_entry_id_team.ids),('is_cheque', '=', True)])
            account_payment_done_team = self.env['account.payment'].search(
                [('move_id', 'in', account_entry_id_team.ids),('pdc_id.state', '=', 'done'),('is_cheque', '=', True)])
            for payment_team in account_payment_team:
                payment_amount_team += payment_team.amount
            for payment_done_team in account_payment_done_team:
                payment_amount_team -= payment_done_team.pdc_id.payment_amount

            invoiced_amount_team = invoiced_amount_team + payment_amount_team
            credit_team = invoiced_amount_team

            # Sale Orders
            order_id_all = self.env['sale.order'].search([  ('partner_id', 'in', partner_ids),
                                                            ('type_id.is_credit_limit', '=', True),
                                                            ('state', 'in', ('sale', 'done'))])
            sale_order_amount_all = 0
            sale_order_amount_all_cash = 0
            order = []
            for sale in order_id_all:
                if sale.id not in order:
                    if sale.invoice_status != 'invoiced':
                        order.append(sale.id)
                        if sale.payment_term_id and sale.payment_term_id.is_cash == False:
                            if sale.invoice_count == 0:
                                sale_order_amount_all += sale.amount_total
                            else:
                                total_invoice = 0
                                for inv in sale.invoice_ids:
                                    if inv.state != 'cancel':
                                        total_invoice += inv.amount_total
                                sale_order_amount_all += (sale.amount_total - total_invoice)

                        elif sale.payment_term_id and sale.payment_term_id.is_cash == True:
                            if sale.invoice_count == 0:
                                sale_order_amount_all_cash += sale.amount_total
                            else:
                                total_invoice_cash = 0
                                for inv in sale.invoice_ids:
                                    if inv.state != 'cancel':
                                        total_invoice_cash += inv.amount_total
                                sale_order_amount_all_cash += (sale.amount_total - total_invoice_cash)

            # Invoices (draft)
            invoiced_amount_draft = 0.0
            invoiced_amount_draft_cash = 0.0
            invoice = []
            account_id_credit = self.env['account.move'].search([  ('partner_id', 'in', partner_ids),('is_cash', '=', False),
                                                            ('state', '=', 'draft'), ('move_type', '=', 'out_invoice')])
            invoiced_amount = 0
            for acc in account_id_credit:
                if acc.id not in invoice:
                    invoice.append(acc.id)
                    invoiced_amount += acc.amount_total
            invoiced_amount_draft = invoiced_amount

            account_id_cash = self.env['account.move'].search([('partner_id', '=', partner_ids),
                                                      ('state', '=', 'draft'), ('move_type', '=', 'out_invoice'),('is_cash', '=', True)])
            invoiced_amount_cash = 0
            for acc_cash in account_id_cash:
                if acc_cash.id not in invoice:
                    invoice.append(acc_cash.id)
                    invoiced_amount_cash += acc_cash.amount_total

            invoiced_amount_draft_cash = invoiced_amount_cash

            # Post Operation
            credit = "{:.2f}".format(credit)
            credit_team = "{:.2f}".format(credit_team)
            cash = "{:.2f}".format(cash)
            sale_order_amount_all = "{:.2f}".format(sale_order_amount_all)
            sale_order_amount_all_cash = "{:.2f}".format(sale_order_amount_all_cash)
            invoiced_amount_draft = "{:.2f}".format(invoiced_amount_draft)
            invoiced_amount_draft_cash = "{:.2f}".format(invoiced_amount_draft_cash)

            credit = float(credit)
            credit_team = float(credit_team)
            cash = float(cash)
            sale_order_amount_all = float(sale_order_amount_all)
            sale_order_amount_all_cash = float(sale_order_amount_all_cash)
            invoiced_amount_draft = float(invoiced_amount_draft)
            invoiced_amount_draft_cash = float(invoiced_amount_draft_cash)
            
            available_credit = partner_id.credit_limit
            
            credit_team_remain = 0
            credit_limit_show_team = 0
            sale_team_id = False
            cash_check = False
            if customer_credit_id:
                sale_team_id = customer_credit_id.credit_id.credit_line.filtered(lambda l: l.sale_team_id == self.team_id)
                if sale_team_id:
                    credit_team_remain = sale_team_id.credit_remain
                    credit_limit_show_team = sale_team_id.credit_limit
            if self.payment_term_id.is_cash is True :
                available_cash = partner_id.cash_limit
                if self.amount_total > available_cash :
                    cash_check = True
            available_credit_sale_team = credit_team_remain
    
            if ((self.amount_total > available_credit or (self.amount_total > available_credit_sale_team and sale_team_id)) and self.payment_term_id.is_cash == False) or cash_check:
                imd = self.env['ir.model.data'].sudo()
                exceeded_amount = partner_id.credit_limit - self.amount_total
                exceeded_amount_cash = partner_id.cash_limit
                if cash_check:
                    exceeded_amount_cash = partner_id.cash_limit - self.amount_total
                    wizard_name = "Cash Limit"

                exceeded_amount_team = credit_team_remain - self.amount_total

                exceeded_amount = "{:.2f}".format(exceeded_amount)
                exceeded_amount = float(exceeded_amount)
                exceeded_amount_cash = "{:.2f}".format(exceeded_amount_cash)
                exceeded_amount_cash = float(exceeded_amount_cash)
                exceeded_amount_team = "{:.2f}".format(exceeded_amount_team)
                exceeded_amount_team = float(exceeded_amount_team)

                is_cash = False
                if self.payment_term_id:
                    is_cash = self.payment_term_id.is_cash
                if partner_id.credit_type == 'new':
                    vals_wiz = {
                        'partner_id': partner_id.id,'is_cash':is_cash,
                        'sale_orders': str(len(order)) + ' Worth Cash: ' + str(sale_order_amount_all_cash),
                        'invoices': str(len(invoice)) + ' Worth Cash: ' + str(invoiced_amount_draft_cash),
                        'current_sale': self.amount_total or 0.0, 'exceeded_amount': exceeded_amount,'exceeded_amount_cash':exceeded_amount_cash,
                        'cash':cash,'credit_limit_on_hold': partner_id.credit_limit_on_hold,
                        'team_id':self.team_id.id,'credit_limit_show_team':credit_limit_show_team,'credit_team_remain':credit_team_remain,'credit_team':credit_team,'exceeded_amount_team':exceeded_amount_team,
                        }
                else:
                    vals_wiz = {
                        'partner_id': partner_id.id,'is_cash':is_cash,
                        'sale_orders': str(len(order)) + ' Sale Order Worth Credit: ' + str(sale_order_amount_all) + ' Worth Cash: ' + str(sale_order_amount_all_cash),
                        'invoices': str(len(invoice)) + ' Draft Invoice Worth Credit: ' + str(invoiced_amount_draft) + ' Worth Cash: ' + str(invoiced_amount_draft_cash),
                        'current_sale': self.amount_total or 0.0, 'exceeded_amount': exceeded_amount,'exceeded_amount_cash':exceeded_amount_cash,
                        'credit': credit,'cash':cash,'credit_limit_on_hold': partner_id.credit_limit_on_hold,
                        'team_id':self.team_id.id,'credit_limit_show_team':credit_limit_show_team,'credit_team_remain':credit_team_remain,'credit_team':credit_team,'exceeded_amount_team':exceeded_amount_team,
                        }
                wiz_id = self.env['customer.limit.wizard'].create(vals_wiz)
                # action = imd.xmlid_to_object('dev_customer_credit_limit.action_customer_limit_wizard')
                # form_view_id = imd.xmlid_to_res_id('dev_customer_credit_limit.view_customer_limit_wizard_form')
                action = self.env["ir.actions.actions"]._for_xml_id("dev_customer_credit_limit.action_customer_limit_wizard")
                action['views'] = [(self.env.ref('dev_customer_credit_limit.view_customer_limit_wizard_form').id, 'form')]
                action['context'] = {'order_id': self.id}
                action['res_id'] = wiz_id.id
                wizard_name = action['name']
                if self.payment_term_id.is_cash is True :

                    wizard_name = "Cash Limit Exceeded"
                action['name'] = wizard_name
                return action
                # return {
                #     'name': wizard_name, 'help': action.help, 'type': action.type,
                #     'views': [(form_view_id, 'form')],
                #     'view_id': form_view_id, 
                #     'target': action.target,
                #     # 'context': action.context, 
                #     'context': {'order_id': self.id}, 
                #     'res_model': action.res_model, 'res_id': wiz_id.id,
                #     }
            else:
                return self.action_confirm()
        elif self.type_id.pass_credit_limit is False:
            if self.payment_term_id.is_cash is False:
                raise UserError(_("ไม่อนุญาตให้ทำการขาย เนื่องจากเงื่อนไขการชำระเงินไม่ถูกต้อง"))
            else:
                return self.action_confirm()
        else:
            return self.action_confirm()
        # return True

    # ปิดไปใช้ อันใหม่ที่อยู่ใน module hdc_sale_addon onchange_partner_id_team_id_credit_limit() เพราะ ปัญหาลำดับการทำงาน onchange
    # @api.onchange('partner_id')
    # def onchange_partner_id_check_credit_limit(self):
    #     customer_credit_id = self.env["customer.credit.limit"].search([('partner_id', '=', self.partner_id.id)])
    #     if customer_credit_id:
    #         credit_team_remain = 0
    #         sale_team_id = False
    #         if customer_credit_id:
    #             sale_team_id = customer_credit_id.credit_id.credit_line.filtered(lambda l: l.sale_team_id == self.team_id)
    #             if sale_team_id:
    #                 credit_team_remain = sale_team_id.credit_remain

    #         if customer_credit_id.cash_remain <= 0 or credit_team_remain <= 0:
    #             partner_id = self.partner_id

    #             exceeded_amount_team = credit_team_remain - self.amount_total
    #             exceeded_amount_team = "{:.2f}".format(exceeded_amount_team)
    #             exceeded_amount_team = float(exceeded_amount_team)
                
    #             return {
    #                 'warning': {'title': "Credit Limit Warning", 
    #                             'message': 
    #                             "Customer: %s \nCredit Remain: %.2f  \nCash Limit: %.2f \nExceeded Amount (Credit): %.2f "  
    #                             % (partner_id.name, credit_team_remain ,partner_id.cash_limit ,exceeded_amount_team),
    #                             },
    #             }

    @api.depends("partner_id", "credit_limit_on_hold")
    def _compute_check_credit_limit_on_hold(self):
        for rec in self:
            if rec.partner_id.credit_limit_on_hold == True:
                rec.check_credit_limit_on_hold = True
            else:
                if rec.credit_limit_on_hold == True:
                    rec.check_credit_limit_on_hold = True
                else:
                    rec.check_credit_limit_on_hold = False

    def _compute_so_invoice_amount(self):
        for rec in self:
            invoice_amount_total_sum = 0 
            for invoice in rec.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice' and inv.state != 'cancel'):
                invoice_amount_total_sum += invoice.amount_total
            rec.so_invoice_amount = invoice_amount_total_sum
    

    def get_check_credit_exceed(self):
        customer_credit_id = self.env["customer.credit.limit"].search([('partner_id', '=', self.partner_id.id)])
        check_credit_exceed = False
        check_cash_exceed = False
        if customer_credit_id:
            if self.approve_credit_amount > 0:
                remain_total = self.amount_total - self.so_invoice_amount
                remain_approve = self.approve_credit_amount - self.so_invoice_amount
                if remain_total > remain_approve:
                    if self.payment_term_id.is_cash is True:
                        check_cash_exceed = True
                    else:
                        check_credit_exceed = True
            else:
                available_credit = self.partner_id.credit_limit
                credit_team_remain = 0
                sale_team_id = False
                cash_check = False
                if customer_credit_id:
                    sale_team_id = customer_credit_id.credit_id.credit_line.filtered(lambda l: l.sale_team_id == self.team_id)
                    if sale_team_id:
                        credit_team_remain = sale_team_id.credit_remain
                    if self.payment_term_id.is_cash is True :
                        available_cash = self.partner_id.cash_limit
                        if available_cash < 0:
                            cash_check = True
                available_credit_sale_team = credit_team_remain
                if (( available_credit < 0 or (available_credit_sale_team < 0 and sale_team_id)) and self.payment_term_id.is_cash == False) or cash_check:
                    if cash_check:
                        check_cash_exceed = True
                    else:
                        check_credit_exceed = True
        else:
            if self.payment_term_id.is_cash is True :
                if self.approve_credit_amount > 0:
                    remain_total = self.amount_total - self.so_invoice_amount
                    if remain_total > self.approve_credit_amount:
                        if self.payment_term_id.is_cash is True:
                            check_cash_exceed = True
                        else:
                            check_credit_exceed = True
                else:
                    available_cash = self.partner_id.cash_limit
                    if available_cash < 0:
                        check_cash_exceed = True
        return check_credit_exceed,check_cash_exceed
    
    def _compute_check_credit_exceed(self):
        for rec in self:
            check_credit_exceed,check_cash_exceed = rec.get_check_credit_exceed()
            rec.check_credit_exceed = check_credit_exceed
            rec.check_cash_exceed = check_cash_exceed
            
    def create_temp_credit_request(self):
        for order in self:
            self.env['temp.credit.request'].create({
                'order_no': order.id,
                'partner_id': order.partner_id.id,
                'sale_person': order.user_id.id,
                'sale_team_id': order.team_id.id,
            })

    def write(self, values):
        start_state = self.state
        res = super(SaleOrder, self).write(values)
        if self.type_id.is_credit_limit == True and start_state in ['sale']:
            if abs(self.old_total_price - self.amount_total) > 0.009:
                check_credit_exceed,check_cash_exceed = self.get_check_credit_exceed()
                if self.payment_term_id.is_cash is True :
                    check_credit_exceed = False
                else:
                    check_cash_exceed = False
                
                if check_cash_exceed == True or check_credit_exceed == True:
                    self.update({'state': 'credit_limit'})
                    temp_credit_id = self.env['temp.credit.request'].search([('order_no','=',self.id)])
                    if temp_credit_id:
                        temp_credit_id.state = 'waiting_approval'
                    else:
                        self.create_temp_credit_request()
                self.update({'old_total_price': self.amount_total})
        return res
    
    @api.onchange('payment_term_id')
    def _onchange_payment_term_id_change_validity_date(self):
        if self.payment_term_id and self.payment_term_id.days:
            self.validity_date = date.today() + timedelta(days=self.payment_term_id.days)