# Copyright 2023 Basic Solution Co., Ltd. (www.basic-solution.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models,exceptions
from odoo.exceptions import UserError, ValidationError, AccessError


class AccountMoveLine(models.Model):
    _inherit = "pdc.wizard"

    check_pay_in_id = fields.Many2one(
        comodel_name="account.check.pay.in",
        string="Post Date Cheque",
        copy=False,
        store=True,
        check_company=True,
    )
    check_deposit = fields.Many2one('account.check.pay.in', string="Check Deposit")

class AccountCheckPayIn(models.Model):
    _name = "account.check.pay.in"
    _description = "Account Check Pay In"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "deposit_date desc"
    _check_company_auto = True
        
    name = fields.Char(string="Name", size=64, readonly=True, default="/", copy=False)
    
    pdc_wizard_ids = fields.Many2many(comodel_name="pdc.wizard",
        inverse_name="check_pay_in_id",string="Check Registered",
        states={"done": [("readonly", "=", True)]},
        domain="[('state', '=', 'registered'),('payment_type', '=', 'receive_money'),('check_deposit', '=', False), ('company_id', '=', company_id)]",
        store=True
        )
            
    deposit_date = fields.Date(
        string="Deposit Date",
        required=True,
        states={"done": [("readonly", "=", True)]},
        default=fields.Date.context_today,
        tracking=True,
        store=True,
        copy=False,
        help="วันที่นำฝากเช็ค"
    )

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        domain="[('company_id', '=', company_id)]",
        required=True,
        store=True,
        check_company=True,
        states={"done": [("readonly", "=", True)]},
        tracking=True,
    ) 
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        store=True,
        states={"done": [("readonly", "=", True)]},
        default=lambda self: self.env.company,
        tracking=True,)

    state = fields.Selection(
        selection=[("draft", "Draft"), ("done", "Done")],
        string="Status",
        default="draft",
        store=True,
        readonly=True,
        tracking=True,
    )

    payment_total_amount = fields.Float("Total Amount", compute="_check_payment_total", default=0)

    @api.onchange('pdc_wizard_ids')
    def _check_payment_total(self):
        for record in self:
            selected_bid_lines = record.pdc_wizard_ids.filtered(lambda l: l.payment_amount)
            record.update({
                'payment_total_amount': sum(selected_bid_lines.mapped("payment_amount"))
            })
    
    @api.onchange('journal_id')
    def change_journal(self):
      if self.journal_id:
        return {'domain': {'pdc_wizard_ids':[('state', '=', 'registered'),('payment_type', '=', 'receive_money'),('check_deposit', '=', False), ('company_id', '=', self.company_id.id)]}}
        # return {'domain': {'pdc_wizard_ids':[('state', '=', 'registered'),('payment_type', '=', 'receive_money'),('check_deposit', '=', False),('journal_id', '=', self.journal_id.id)]}}
      else:
          return {'domain': {'pdc_wizard_ids':[('state', '=', 'registered'),('payment_type', '=', 'receive_money'),('check_deposit', '=', False), ('company_id', '=', self.company_id.id)]}}
    
    def open_pdc_items(self):
        [action] = self.env.ref('sh_pdc.sh_pdc_payment_menu_action').read()
        ids = self.env['pdc.wizard'].search([('id', 'in', self.pdc_wizard_ids.ids)])
        id_list = []
        for pdc_id in ids:
            id_list.append(pdc_id.id)
        action['domain'] = [('id', 'in', id_list)]
        return action

    # Change State Registered.
    def change_back_to_draft_pdc(self):
        for record in self:
            check_pdc_line = record.pdc_wizard_ids
            if check_pdc_line:
                id_check_register_line = check_pdc_line.ids

                check_done_state = self.env['pdc.wizard'].search([('id', 'in', id_check_register_line), ('state', '=', 'done')])
                if check_done_state:
                    raise exceptions.UserError(
                    _("มี PDC บางใบอยู่ในสถานะ Done")
                )
                else:
                    print("Success")
                    check_pdc_line.write({'state': 'registered'})
            else:
                print("Not Found") #Not Found



    def backtodraft(self):
        self.write({"state": "draft"})
        self.change_back_to_draft_pdc()

    @api.model
    def create(self, vals):
        if "company_id" in vals:
            self = self.with_company(vals["company_id"])
        if vals.get("name", "/") == "/":
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "account.check.pay.in", vals.get("deposit_date")
            )
        res = super().create(vals)
        if len(res.pdc_wizard_ids) > 0:
            pdc_ids = self.env['pdc.wizard'].search([('id', 'in', res.pdc_wizard_ids.ids)])
            if pdc_ids:
                for pdc_id in pdc_ids:
                    pdc_id.write({
                        'check_deposit': res.id
                    })
        return res
    
    def write(self, vals):
        if vals.get('pdc_wizard_ids'):
            # loop set deposit
            for val_new in vals.get('pdc_wizard_ids')[0][2]:
                if self.pdc_wizard_ids:
                    for val_old in self.pdc_wizard_ids:
                        if not val_old == val_new:
                            pdc = self.env['pdc.wizard'].search([('id', '=', val_new)])
                            if pdc:
                                pdc.write({'check_deposit': self.id})
                else:
                    pdc = self.env['pdc.wizard'].search([('id', '=', val_new)])
                    if pdc:
                        pdc.write({'check_deposit': self.id})
            # loop delete deposit
            all = self.pdc_wizard_ids.ids
            for val_new in vals.get('pdc_wizard_ids')[0][2]:
                for val_old in self.pdc_wizard_ids:
                    if val_old.id == val_new:
                        all.remove(val_old.id)
            if len(all) > 0:
                pdc = self.env['pdc.wizard'].search([('id', 'in', all)])
                if pdc:
                    for pdc_id in pdc:
                        pdc_id.write({'check_deposit': False})
        return super().write(vals)
    
    
    # Change State Deposited.
    def change_validate_pdc(self):
        check_pdc_line = self.pdc_wizard_ids

        if check_pdc_line:
            id_check_register_line = self.pdc_wizard_ids.ids
            check_register_state = self.env['pdc.wizard'].search([('id', '=', id_check_register_line)])
            
            if check_register_state:
                for pdc in check_register_state:
                    if pdc.state != 'registered':
                        raise exceptions.UserError("เฉพาะ Registered PDC เท่านั้นที่สามารถนำฝากได้")

                #after check state Register
                print("Success")
                check_register_state.write({'state': 'deposited'})
                check_register_state.write({'journal_id': self.journal_id})
                self.write({'state': 'done'})
            else:
                raise exceptions.UserError("เฉพาะ Registered PDC เท่านั้นที่สามารถนำฝากได้")
        else:
            raise exceptions.UserError("Not Found PDC")

    def validate_deposit(self):
        # self.write({"state": "done"})
        self.change_validate_pdc()
        
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ajo = self.env["account.journal"]
        company_id = res.get("company_id")
        # pre-set journal_id and bank_journal_id is there is only one
        domain = [("company_id", "=", company_id), ("type", "=", "bank")]
        journals = ajo.search(domain)
        if len(journals) == 1:
            res["journal_id"] = journals.id
        return res