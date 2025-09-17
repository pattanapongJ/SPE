# Copyright (C) Softhealer Technologies.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.http import request
from datetime import timedelta,datetime,date



class Attachment(models.Model):
    _inherit = 'ir.attachment'

    pdc_id = fields.Many2one('pdc.wizard')
    
class AccountCheckPayIn(models.Model):
    _name = "account.check.pay.in"
    
class AccountJournal(models.Model):
    _inherit = "account.journal"
    
    pdc_journal_checkbox = fields.Boolean(string="PDC Journal", default=False) 

class PDC_wizard(models.Model):
    _name = "pdc.wizard"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "PDC Wizard"
    
    
    
    
    #Basic- Addition Field Effective Date on Action Button Bounce, Cancel for Posted Accounting Date Bounce, Cancel.
    pdc_bounce_date = fields.Date(
        string='Bounce Date',
        store =True,
        index=True,
        help="วันที่เช็คส่งคืน")
    
    #Basic- Addition Field Cheque Date on PDC Payment.
    pdc_cheque_date = fields.Date(
        string='Cheque Date',
        store =True,
        index=True,
        help="วันที่หน้าเช็ค",
        default=fields.Date.context_today)
    
    #Basic- Addition Field Effective Date on PDC Payment.
    pdc_effective_date = fields.Date(
        string='Effective Date',
        store =True,
        index=True,
        help="วันที่เช็คเคลียร์ริ่ง (จะใช้วันที่นี้ในการบันทึกบัญชีเมื่อเช็คเคลียร์ริ่ง",
        default=fields.Date.context_today)
    
    #Basic- Addition Field Bounce Reason for Reason of Cheque Status Bounce.
    pdc_bounce_reason = fields.Char(
        string='Bounce Reason',
        store =True,
        help="สาเหตุของการเกิดเช็คส่งคืน",
        index=True,)
    
    # payment_number = fields.Many2one('account.payment', string='Payment Number')
    
    def save_create_pdc(self):
        # อัปเดตฟิลด์ pdc_id ในฟอร์ม account.payment
        account_payment = self.env['account.payment'].browse(self._context.get('active_id'))
        account_payment.pdc_id = self.id
        
    

    #pdc only be allowed to delete in draft state
    def unlink(self):
        
        for rec in self:
            if rec.state != 'draft':
                raise UserError("You can only delete draft state pdc")

        return super(PDC_wizard, self).unlink()

    def action_register_check(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        account_move_model = self.env[active_model].browse(active_id)
        
        if account_move_model.move_type not in ('out_invoice','in_invoice'):
            raise UserError("Only Customer invoice and vendor bills are considered!")

        move_listt = []
        payment_amount = 0.0
        payment_type = ''
        if len(active_ids) > 0:
            account_moves = self.env[active_model].browse(active_ids)
            partners = account_moves.mapped('partner_id')
            if len(set(partners)) != 1:
                raise UserError('Partners must be same')

            states = account_moves.mapped('state')
            if len(set(states)) != 1 or states[0] != 'posted':
                raise UserError('Only posted invoices/bills are considered for PDC payment!!')

            for account_move in account_moves:
                if account_move.payment_state != 'paid' and account_move.amount_residual != 0.0:
                    payment_amount = payment_amount + account_move.amount_residual
                    move_listt.append(account_move.id)

        if not move_listt:
            raise UserError("Selected invoices/bills are already paid!!")

        if account_moves[0].move_type in ('in_invoice'):
            payment_type = 'send_money'
        
        if account_moves[0].move_type in ('out_invoice'):
            payment_type = 'receive_money'

        
        return {
            'name': 'PDC Payment',
            'res_model': 'pdc.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('sh_pdc.sh_pdc_wizard_form_wizard').id,
            'context':{
                'default_invoice_ids':[(6,0,move_listt)],
                'default_partner_id': account_move_model.partner_id.id,
                'default_payment_amount':payment_amount,
                'default_payment_type': payment_type
            },
            'target': 'new',
            'type': 'ir.actions.act_window'
        }

    def open_payment(self):
        [action] = self.env.ref('sh_pdc.sh_pdc_payment_in_menu_action').read()
        ids = self.env['account.payment'].search([('pdc_id', 'in', self.ids)])
        id_list = []
        for pdc_id in ids:
            id_list.append(pdc_id.id)
        action['domain'] = [('id', 'in', id_list)]
        return action

    def open_attachments(self):
        [action] = self.env.ref('base.action_attachment').read()
        ids = self.env['ir.attachment'].search([('pdc_id', '=', self.id)])
        id_list = []
        for pdc_id in ids:
            id_list.append(pdc_id.id)
        action['domain'] = [('id', 'in', id_list)]
        return action

    def open_journal_items(self):
        [action] = self.env.ref('account.action_account_moves_all').read()
        ids = self.env['account.move.line'].search([('pdc_id', '=', self.id)])
        id_list = []
        for pdc_id in ids:
            id_list.append(pdc_id.id)
        action['domain'] = [('id', 'in', id_list)]
        return action

    def open_journal_entry(self):
        [action] = self.env.ref(
            'sh_pdc.sh_pdc_action_move_journal_line').read()
        ids = self.env['account.move'].search([('pdc_id', '=', self.id)])
        id_list = []
        for pdc_id in ids:
            id_list.append(pdc_id.id)
        action['domain'] = [('id', 'in', id_list)]
        return action

    @api.model
    def default_get(self, fields):
        rec = super(PDC_wizard, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')

        # Check for selected invoices ids
        if not active_ids or active_model != 'account.move':
            return rec
        invoices = self.env['account.move'].browse(active_ids)
        if invoices:
            invoice = invoices[0]
            if invoice.move_type in ('out_invoice', 'out_refund'):
                rec.update({'payment_type': 'receive_money'})
            elif invoice.move_type in ('in_invoice', 'in_refund'):
                rec.update({'payment_type': 'send_money'})

            rec.update({'partner_id': invoice.partner_id.id,
                        'payment_amount': invoice.amount_residual,
                        'invoice_id': invoice.id,
                        'due_date': invoice.invoice_date_due,
                        'memo': invoice.name})

        return rec

    name = fields.Char("Name", default='New', readonly=1,tracking=True)
    #check_amount_in_words = fields.Char(string="Amount in Words",compute='_compute_check_amount_in_words')
    payment_type = fields.Selection([('receive_money', 'Receive Money'), (
        'send_money', 'Send Money')], string="Payment Type", default='receive_money',tracking=True)
    partner_id = fields.Many2one('res.partner', string="Partner",tracking=True)
    payment_amount = fields.Monetary("PDC Amount",tracking=True)
    currency_id = fields.Many2one(
        'res.currency', string="Currency", default=lambda self: self.env.company.currency_id,tracking=True)
    reference = fields.Char("Cheque Reference",help="บันทึกเลขที่เช็ค",tracking=True)
    journal_id = fields.Many2one('account.journal', string="Bank Journal", domain=[
                                 ('type', '=', 'bank')],tracking=True)
    cheque_status = fields.Selection([('draft','Draft'),('deposit','Deposit'),('paid','Paid')],string="Cheque Status",default='draft',tracking=True)
    payment_date = fields.Date(
        "PDC Date", default=fields.Date.context_today , required=1,help="วันที่รับ/จ่าย เช็ค",tracking=True)
    due_date = fields.Date("Due Date",help="วันที่หน้าเช็ค",tracking=True)
    memo = fields.Char("Memo",tracking=True)
    agent = fields.Char("Agent",tracking=True)
    bank_id = fields.Many2one('res.bank', string="Bank",tracking=True ,help="ธนาคารของเช็ค")
    bank_branch = fields.Char("Bank Branch",help="สาขาธนาคารของเช็ค")
    attachment_ids = fields.Many2many('ir.attachment', string='Cheque Image')
    company_id = fields.Many2one('res.company',string='company',default=lambda self: self.env.company,tracking=True)
    invoice_id = fields.Many2one('account.move', string="Invoice/Bill",tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('registered', 'Registered'), ('returned', 'Returned'),
                              ('deposited', 'Deposited'), ('bounced', 'Bounced'), ('done', 'Done'), ('cancel', 'Cancelled')], string="State", default='draft',tracking=True)

    deposited_debit = fields.Many2one('account.move.line')
    deposited_credit = fields.Many2one('account.move.line')

    invoice_ids = fields.Many2many('account.move')
    account_move_ids = fields.Many2many('account.move',compute="compute_account_moves",)
    done_date = fields.Date(string = "Done Date",readonly=True,tracking=True)
    

    @api.depends('payment_type','partner_id')
    def compute_account_moves(self):
        
        self.account_move_ids = False
        domain = [('partner_id','=',self.partner_id.id),('payment_state','!=','paid'),('amount_residual','!=',0.0),('state','=','posted')]

        if self.payment_type == 'receive_money':
            domain.extend([('move_type', '=','out_invoice')])
        
        else:
            domain.extend([('move_type', '=','in_invoice')])

        moves = self.env['account.move'].search(domain)
        self.account_move_ids = moves.ids
        
    #attachment_ids = fields.One2many(
    #    'ir.attachment', 'pdc_id', string="Attachments")

#     def _compute_check_amount_in_words(self):
#         if self:
#             for rec in self:
#                 rec.check_amount_in_words = False
#                 rec.check_amount_in_words = rec.currency_id.amount_to_text(rec.payment_amount)
                
    # # Check State PDC
    # @api.onchange('state')
    # def check_pdc_state(self):
    #     pdc_state = self.state
    #     print("Check")
        
    #     for state in self:
    #         if pdc_state == 'registered' or pdc_state == 'done':
    #             id_pdc_cheque_payment = self.id
    #             check_state_pdc_no = self.env['account.payment'].search([('pdc_id.id', '=', id_pdc_cheque_payment)], limit=1)
    #             print( pdc_state , " Found State PDC No.")
    #             print( check_state_pdc_no , " Found State PDC No.")
    #         else:
    #             print( pdc_state , " Not Found State PDC No.")
    

                
    # Register pdc payment
    def button_register(self):
        listt = []
        if self:
            
            if self.invoice_id:
                listt.append(self.invoice_id.id)
            if self.invoice_ids:
                listt.extend(self.invoice_ids.ids)

            self.write({
                'invoice_ids' : [(6,0,list(set(listt)))]
            })

            if self.cheque_status == 'draft':
                self.write({'state':'draft'})
            
            if self.cheque_status == 'deposit':
                self.action_register()
                self.action_deposited()
                self.write({'state':'deposited'})
            
            if self.cheque_status == 'paid':
                self.action_register()
                self.action_deposited()
                self.action_done()
                self.write({'state':'done'})
            
#             if self.invoice_id:
#                 self.invoice_id.sudo().write({
# #                     'amount_residual_signed': self.invoice_id.amount_residual_signed - self.payment_amount,
#                     'amount_residual':self.invoice_id.amount_residual - self.payment_amount,
#                     })
#                 self.invoice_id._compute_amount()
#
        #action_register
    def action_deposited(self):
        self.write({'state': 'deposited'})

    def check_payment_amount(self):
        if self.payment_amount <= 0.0:
            raise UserError("Amount must be greater than zero!")

    def check_pdc_account(self):
        if self.payment_type == 'receive_money':
            if not self.env.company.pdc_customer:
                raise UserError(
                    "Please Set PDC payment account for Customer !")
            else:
                return self.env.company.pdc_customer.id

        else:
            if not self.env.company.pdc_vendor:
                raise UserError(
                    "Please Set PDC payment account for Supplier !")
            else:
                return self.env.company.pdc_vendor.id

    def get_partner_account(self):
        if self.payment_type == 'receive_money':
            return self.partner_id.property_account_receivable_id.id
        else:
            return self.partner_id.property_account_payable_id.id

    def action_returned(self):
        self.check_payment_amount()
        self.write({'state': 'returned'})

###Additional get detail of post accounting
    #payment_effective_date
    def get_credit_move_line_effective_date(self, account):
        return {
            'pdc_id': self.id,
#             'partner_id': self.partner_id.id,
            'account_id': account,
            'credit': self.payment_amount,
            'ref': self.memo,
            'date': self.pdc_effective_date,
            'date_maturity': self.due_date,
        }
        
    #payment_effective_date
    def get_debit_move_line_effective_date(self, account):
        return {
            'pdc_id': self.id,
#             'partner_id': self.partner_id.id,
            'account_id': account,
            'debit': self.payment_amount,
            'ref': self.memo,
            'date': self.pdc_effective_date,
            'date_maturity': self.due_date,
        }
        
    def get_move_vals_effective_date(self, debit_line, credit_line):
        return {
            'pdc_id': self.id,
            'date': self.pdc_effective_date,
            'journal_id': self.journal_id.id,
#             'partner_id': self.partner_id.id,
            'ref': self.memo,
            'line_ids': [(0, 0, debit_line),
                         (0, 0, credit_line)]
        }

    #payment_due_date
    def get_credit_move_line_due_date(self, account):
        return {
            'pdc_id': self.id,
#             'partner_id': self.partner_id.id,
            'account_id': account,
            'credit': self.payment_amount,
            'ref': self.memo,
            'date': self.due_date,
            'date_maturity': self.due_date,
        }
        
    #payment_due_date
    def get_debit_move_line_due_date(self, account):
        return {
            'pdc_id': self.id,
#             'partner_id': self.partner_id.id,
            'account_id': account,
            'debit': self.payment_amount,
            'ref': self.memo,
            'date': self.due_date,
            'date_maturity': self.due_date,
        }
        
    def get_move_vals_due_date(self, debit_line, credit_line):
        return {
            'pdc_id': self.id,
            'date': self.due_date,
            'journal_id': self.journal_id.id,
#             'partner_id': self.partner_id.id,
            'ref': self.memo,
            'line_ids': [(0, 0, debit_line),
                         (0, 0, credit_line)]
        }

    #payment_date
    def get_credit_move_line(self, account):
        return {
            'pdc_id': self.id,
#             'partner_id': self.partner_id.id,
            'account_id': account,
            'credit': self.payment_amount,
            'ref': self.memo,
            'date': self.payment_date,
            'date_maturity': self.due_date,
        }
        
    #payment_date
    def get_debit_move_line(self, account):
        return {
            'pdc_id': self.id,
#             'partner_id': self.partner_id.id,
            'account_id': account,
            'debit': self.payment_amount,
            'ref': self.memo,
            'date': self.payment_date,
            'date_maturity': self.due_date,
        }

    def get_move_vals(self, debit_line, credit_line):
        return {
            'pdc_id': self.id,
            'date': self.payment_date,
            'journal_id': self.journal_id.id,
#             'partner_id': self.partner_id.id,
            'ref': self.memo,
            'line_ids': [(0, 0, debit_line),
                         (0, 0, credit_line)]
        }
        
    # Check State PDC NO.
    def check_state_pdc_no(self):
        pdc_state = self.state   
        for state in self:
            if pdc_state == 'registered' or pdc_state == 'done':
                id_pdc_cheque_payment = self.id
                check_state_pdc_no = self.env['account.payment'].search([('pdc_id', '=', id_pdc_cheque_payment)], limit=1)
                # print( pdc_state , " Found State PDC No.")
                if check_state_pdc_no:
                    print("Success")
                    check_state_pdc_no.write({'check_pdc_state': pdc_state})
                else:
                    print("Not Found PDC")
                
            else:
                print( pdc_state , " Not Found State PDC No.")

    def action_register(self):
        #registered
        # pdc_payments = self.env['account.payment'].search([('pdc_id', 'in', self.ids)])
        pdc_payments = self.env['account.payment'].search([('pdc_id', 'in', self.ids)])
        total_payment_amount = sum(pdc_payment.amount for pdc_payment in pdc_payments)
        
        if self.payment_amount == total_payment_amount:
                    for payment in self:
                        pdc_payments = self.env['account.payment'].search([('pdc_id', 'in', self.ids)])
                        if pdc_payments:
                            all_conditions_passed = True  # สร้างตัวแปรสำหรับตรวจสอบเงื่อนไขทั้งหมด
                            
                            for pdc_payment in pdc_payments:
                                # if pdc_payment.amount != payment.payment_amount:
                                #     all_conditions_passed = False
                                #     raise UserError(_("PDC Amount is not equal to the total Related Payment Amount"))
                                if not payment.partner_id:
                                    all_conditions_passed = False
                                    raise UserError(_("Please enter Partner in PDC"))    
                                elif not payment.reference:
                                    all_conditions_passed = False
                                    raise UserError(_("Please enter Check Reference in PDC"))          
                                elif not payment.due_date:
                                    all_conditions_passed = False
                                    raise UserError(_("Please enter Due Date in PDC"))
                                elif pdc_payment.payment_type != payment.payment_type:
                                    if (
                                        (pdc_payment.payment_type == 'inbound' and payment.payment_type != 'receive_money') or
                                        (pdc_payment.payment_type == 'outbound' and payment.payment_type != 'send_money')
                                    ):
                                        all_conditions_passed = False
                                        raise UserError(_("Payment type is not match"))
                                elif payment.journal_id:
                                    # เช็ค Journal
                                    journal = payment.journal_id
                                    check_pdc_journal = self.env['account.journal'].search([('id', '=', journal.id), ('pdc_journal_checkbox', '=', True)])
                                    if not check_pdc_journal:
                                        all_conditions_passed = False
                                        raise UserError(_("Payment Journal is not PDC Journal"))
                            
                            if all_conditions_passed:
                                print("Success ************************************")
                                self.write({'state': 'registered'}) 
                                # Check State PDC NO. 
                                self.check_state_pdc_no()  

        else:
            raise UserError(_("Total Payment Amount is not equal to the PDC Amount"))
        
    def action_bounced(self):
        self.write({'state': 'bounced'})

    def action_done(self):
        move = self.env['account.move']

        self.check_payment_amount()  # amount must be positive
        pdc_account = self.check_pdc_account()
        bank_account = self.journal_id.payment_debit_account_id.id or self.journal_id.payment_credit_account_id.id

        # Create Journal Item
        move_line_vals_debit = {}
        move_line_vals_credit = {}
        if self.payment_type == 'receive_money':
            move_line_vals_debit = self.get_debit_move_line_effective_date(bank_account)
            move_line_vals_credit = self.get_credit_move_line_effective_date(pdc_account)
        else:
            move_line_vals_debit = self.get_debit_move_line_effective_date(pdc_account)
            move_line_vals_credit = self.get_credit_move_line_effective_date(bank_account)

        if self.memo:
            move_line_vals_debit.update({'name': 'PDC Payment :' + self.memo, 'partner_id': self.partner_id.id})
            move_line_vals_credit.update({'name': 'PDC Payment :' + self.memo, 'partner_id': self.partner_id.id})
        else:
            move_line_vals_debit.update({'partner_id': self.partner_id.id})
            move_line_vals_credit.update({'partner_id': self.partner_id.id})

        # related gen reconcile
        # reconcile = self.env['account.full.reconcile'].sudo().create({}).id
        # move_line_vals_credit.update({'full_reconcile_id':reconcile})
        # if self.payment_number:
        #     if self.payment_number.move_id:
        #         if self.payment_number.move_id.line_ids:
        #             for move_line_payment in self.payment_number.move_id.line_ids:
        #                 if move_line_payment.debit > 0:
        #                         move_line_payment.update({'full_reconcile_id':reconcile})
        #         else:
        #             raise UserError('No moving records payment')
        #     else:
        #         raise UserError('Payment Number, There is no reference value in the field (Journal Entry)')
        # else:
        #     raise UserError('There is no reference value in the field (Payment Number)')

        # create move and post it
        move_vals = self.get_move_vals_effective_date(
            move_line_vals_debit, move_line_vals_credit)
        move_id = move.create(move_vals)
        move_id.action_post()

        payment_ids = self.env['account.payment'].search([('pdc_id', '=', self.id)])
        to_reconcile_move_lines = self.env['account.move.line']
        to_reconcile_move_lines |= move_id.line_ids.filtered(
            lambda l: l.account_id.id == pdc_account and not l.reconciled)
        to_reconcile_move_lines |= payment_ids.line_ids.filtered(
            lambda l: l.account_id.id == pdc_account and not l.reconciled)
        if len(to_reconcile_move_lines) > 1:
            to_reconcile_move_lines.reconcile()

        self.write({
            'state': 'done',
            'done_date': date.today(),
        })

        # Check State PDC NO.
        self.check_state_pdc_no()


    def action_cancel(self):
        self.write({'state': 'cancel'})
        
        
    


    @api.model
    def create(self, vals):
        # self.env.ref('sh_pdc.action_id')
        if vals.get('payment_type') == 'receive_money':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'pdc.payment.customer')
        elif vals.get('payment_type') == 'send_money':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'pdc.payment.vendor')

        return super(PDC_wizard, self).create(vals)
    
    
    #==============================
    #    CRON SCHEDULER CUSTOMER
    #==============================
    @api.model
    def notify_customer_due_date(self):
        emails = []
        if self.env.company.is_cust_due_notify:
            notify_day_1 = self.env.company.notify_on_1
            notify_day_2 = self.env.company.notify_on_2
            notify_day_3 = self.env.company.notify_on_3
            notify_day_4 = self.env.company.notify_on_4
            notify_day_5 = self.env.company.notify_on_5
            notify_date_1 = False
            notify_date_2 = False
            notify_date_3 = False
            notify_date_4 = False
            notify_date_5 = False
            if notify_day_1:
                notify_date_1 = fields.date.today() + timedelta(days=int(notify_day_1)*-1)
            if notify_day_2:
                notify_date_2 = fields.date.today() + timedelta(days=int(notify_day_2)*-1)
            if notify_day_3:
                notify_date_3 = fields.date.today() + timedelta(days=int(notify_day_3)*-1)
            if notify_day_4:
                notify_date_4 = fields.date.today() + timedelta(days=int(notify_day_4)*-1)
            if notify_day_5:
                notify_date_5 = fields.date.today() + timedelta(days=int(notify_day_5)*-1)
            
            records = self.search([('payment_type','=','receive_money')])
            for user in self.env.company.sh_user_ids:
                    if user.partner_id and user.partner_id.email:
                        emails.append(user.partner_id.email)
            email_values = {
                'email_to': ','.join(emails),
            }
            view = self.env.ref("sh_pdc.sh_pdc_payment_form_view",raise_if_not_found = False).sudo()
            view_id = view.id if view else 0
            for record in records:
                if (record.due_date == notify_date_1
                    or record.due_date == notify_date_2
                    or record.due_date == notify_date_3
                    or record.due_date == notify_date_4
                    or record.due_date == notify_date_5):
                    
                    if self.env.company.is_notify_to_customer:
                        template_download_id = record.env['ir.model.data'].get_object(
                            'sh_pdc', 'sh_pdc_company_to_customer_notification_1'
                            )
                        _ = record.env['mail.template'].browse(
                            template_download_id.id
                            ).send_mail(record.id,notif_layout='mail.mail_notification_light',force_send=True)
                    if self.env.company.is_notify_to_user and self.env.company.sh_user_ids:
                        url = ''
                        base_url = request.env['ir.config_parameter'].sudo(
                        ).get_param('web.base.url')
                        url = base_url + "/web#id=" + \
                                str(record.id) + \
                                "&&model=pdc.wizard&view_type=form&view_id=" + str(view_id)
                        ctx = {
                            "customer_url": url,
                        }
                        template_download_id = record.env['ir.model.data'].get_object(
                            'sh_pdc', 'sh_pdc_company_to_int_user_notification_1'
                            )
                        _ = request.env['mail.template'].sudo().browse(template_download_id.id).with_context(ctx).send_mail(
                            record.id, email_values=email_values, notif_layout='mail.mail_notification_light', force_send=True)
                        
    
    
    
    #==============================
    #    CRON SCHEDULER VENDOR
    #==============================
    @api.model
    def notify_vendor_due_date(self):
        emails = []
        if self.env.company.is_vendor_due_notify:
            notify_day_1_ven = self.env.company.notify_on_1_vendor
            notify_day_2_ven = self.env.company.notify_on_2_vendor
            notify_day_3_ven = self.env.company.notify_on_3_vendor
            notify_day_4_ven = self.env.company.notify_on_4_vendor
            notify_day_5_ven = self.env.company.notify_on_5_vendor
            notify_date_1_ven = False
            notify_date_2_ven = False
            notify_date_3_ven = False
            notify_date_4_ven = False
            notify_date_5_ven = False
            if notify_day_1_ven:
                notify_date_1_ven = fields.date.today() + timedelta(days=int(notify_day_1_ven)*-1)
            if notify_day_2_ven:
                notify_date_2_ven = fields.date.today() + timedelta(days=int(notify_day_2_ven)*-1)
            if notify_day_3_ven:
                notify_date_3_ven = fields.date.today() + timedelta(days=int(notify_day_3_ven)*-1)
            if notify_day_4_ven:
                notify_date_4_ven = fields.date.today() + timedelta(days=int(notify_day_4_ven)*-1)
            if notify_day_5_ven:
                notify_date_5_ven = fields.date.today() + timedelta(days=int(notify_day_5_ven)*-1)
            
            records = self.search([('payment_type','=','send_money')])
            for user in self.env.company.sh_user_ids_vendor:
                    if user.partner_id and user.partner_id.email:
                        emails.append(user.partner_id.email)
            email_values = {
                'email_to': ','.join(emails),
            }
            view = self.env.ref("sh_pdc.sh_pdc_payment_form_view",raise_if_not_found = False)
            view_id = view.id if view else 0
            for record in records:
                if (record.due_date == notify_date_1_ven
                    or record.due_date == notify_date_2_ven
                    or record.due_date == notify_date_3_ven
                    or record.due_date == notify_date_4_ven
                    or record.due_date == notify_date_5_ven):
                    
                    if self.env.company.is_notify_to_vendor:
                        template_download_id = record.env['ir.model.data'].get_object(
                            'sh_pdc', 'sh_pdc_company_to_customer_notification_1'
                            )
                        _ = record.env['mail.template'].browse(
                            template_download_id.id
                            ).send_mail(record.id,notif_layout='mail.mail_notification_light',force_send=True)
                    if self.env.company.is_notify_to_user_vendor and self.env.company.sh_user_ids_vendor:
                        url = ''
                        base_url = request.env['ir.config_parameter'].sudo(
                        ).get_param('web.base.url')
                        url = base_url + "/web#id=" + \
                                str(record.id) + \
                                "&&model=pdc.wizard&view_type=form&view_id=" + str(view_id)
                        ctx = {
                            "customer_url": url,
                        }
                        template_download_id = record.env['ir.model.data'].get_object(
                            'sh_pdc', 'sh_pdc_company_to_int_user_notification_1'
                            )
                        _ = request.env['mail.template'].sudo().browse(template_download_id.id).with_context(ctx).send_mail(
                            record.id, email_values=email_values, notif_layout='mail.mail_notification_light', force_send=True)



    # Multi Action Starts for change the state of PDC check

    def action_state_draft(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        active_models = self.env[active_model].browse(active_ids)

        for model in active_models:
            if model.state not in ('done','cancel'):                
                raise UserError('Only done and cancel state pdc can reset to draft')

        for model in active_models:
            move_ids = self.env['account.move'].search([('pdc_id', '=', model.id)])
            for move in move_ids:
                move.button_draft()
                lines = self.env['account.move.line'].search([('move_id', '=', move.id)])
                lines.unlink()
                
            model.sudo().write({
                'state':'draft',
                'done_date' : False
                })

            for move in move_ids:
                self.env.cr.execute(""" delete from account_move where id =%s""" %(move.id,))


    def action_state_register(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        
        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')
            
            if len(set(states)) == 1:
                if states[0] == 'draft':
                    for active_model in active_models:
                        active_model.action_register()
                else:
                    raise UserError(
                        "Only Draft state PDC check can switch to Register state!!")
            else:
                raise UserError(
                        "States must be same!!")

    def action_state_return(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] == 'registered':
                    for active_model in active_models:
                        active_model.action_returned()
                else:
                    raise UserError(
                        "Only Register state PDC check can switch to return state!!")
            else:
                raise UserError(
                        "States must be same!!")

    def action_state_deposit(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] in ['registered','returned','bounced']:
                    for active_model in active_models:
                        active_model.action_deposited()
                else:
                    raise UserError(
                        "Only Register,Return and Bounce state PDC check can switch to Deposit state!!")
            else:
                raise UserError(
                        "States must be same!!")
        
    def action_state_bounce(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] == 'deposited':
                    for active_model in active_models:
                        active_model.action_bounced()
                else:
                    raise UserError(
                        "Only Deposit state PDC check can switch to Bounce state!!")
            else:
                raise UserError(
                        "States must be same!!")

    def action_state_done(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] == 'deposited':
                    for active_model in active_models:
                        active_model.action_done()
                else:
                    raise UserError(
                        "Only Deposit state PDC check can switch to Done state!!")
            else:
                raise UserError(
                        "States must be same!!")

    def action_state_cancel(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] in ['registered','returned','bounced']:
                    for active_model in active_models:
                        active_model.action_cancel()
                else:
                    raise UserError(
                        "Only Register,Return and Bounce state PDC check can switch to Cancel state!!")
            else:
                raise UserError(
                        "States must be same!!")