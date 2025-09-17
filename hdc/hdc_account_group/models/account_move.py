# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta
from collections import defaultdict

class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_group_account_line_ids = fields.One2many('invoice.group.account.move.line', 'invoice_group_account_id', string="Invoice Group Account Move Lines")

    # create_check_duplicate_group = fields.Boolean(string="Create Check Duplicate", default=False)
    check_duplicate_group = fields.Boolean(string="Check Duplicate", default=True)

    @api.model
    def create(self, vals):
        vals['check_duplicate_group'] = False
        record = super().create(vals)
        
        account_totals = {}
        for line in record.line_ids:
            account_id = line.account_id.id
            if account_id not in account_totals:
                account_totals[account_id] = {
                    'debit': 0.0,
                    'credit': 0.0,
                    'name': line.name
                }
            
            account_totals[account_id]['debit'] += line.debit
            account_totals[account_id]['credit'] += line.credit
        
        account_lines = []
        for account_id, totals in account_totals.items():
            account_lines.append((0, 0, {
                'invoice_group_account_account_id': account_id,
                'invoice_group_account_label': totals['name'],
                'invoice_group_account_debit': totals['debit'],
                'invoice_group_account_credit': totals['credit'],
            }))
        
        if account_lines:
            record.write({'invoice_group_account_line_ids': account_lines})
            # record.write({'check_duplicate_group': True})

        return record

    def write(self, vals):
        if self.check_duplicate_group:
            account_lines = []
            if 'line_ids' in vals:
                for line_vals in vals['line_ids']:
                    if line_vals[0] == 4:
                        line_data = line_vals[1]
                        move_id = self.env["account.move.line"].browse(line_data)
                        if move_id:
                            account_lines.append((0, 0, {
                                'invoice_group_account_account_id': move_id.account_id.id,
                                'invoice_group_account_label': move_id.name,
                                'invoice_group_account_debit': move_id.debit,
                                'invoice_group_account_credit': move_id.credit,
                            }))
                    elif line_vals[0] == 1:
                        line_id = line_vals[1]
                        line_data = line_vals[2]
                        move_id = self.env["account.move.line"].browse(line_id)
                        account_lines.append((0, 0, {
                           'invoice_group_account_account_id': move_id.account_id.id,
                            'invoice_group_account_label': move_id.name,
                            'invoice_group_account_debit': line_data.get('debit') or 0,
                            'invoice_group_account_credit': line_data.get('credit') or 0,
                        }))
                    elif line_vals[0] == 0:
                        line_data = line_vals[2]
                        account_lines.append((0, 0, {
                            'invoice_group_account_account_id': line_data.get('account_id'),
                            'invoice_group_account_label': line_data.get('name'),
                            'invoice_group_account_debit': line_data.get('debit') or 0,
                            'invoice_group_account_credit': line_data.get('credit') or 0,
                        }))
                    elif line_vals[0] == 6:
                        for line_id in line_vals[2]:
                            move_id = self.env["account.move.line"].browse(line_id)
                            account_lines.append((0, 0, {
                                'invoice_group_account_account_id': move_id.account_id.id,
                                'invoice_group_account_label': move_id.name,
                                'invoice_group_account_debit': move_id.debit,
                                'invoice_group_account_credit': move_id.credit,
                            }))
                    else:
                        pass
                self.invoice_group_account_line_ids.unlink()
                vals['invoice_group_account_line_ids'] = account_lines

        res = super().write(vals)
        return res


    def merge_group_line(self):
        self.check_duplicate_group = False
        account_counts = defaultdict(int)
        new_lines = []  # เก็บรายการใหม่ที่ต้องเพิ่ม

        for line in self.line_ids:
            account_counts[line.account_id.id] += 1

        self.invoice_group_account_line_ids.unlink()

        for acc_id, count in account_counts.items():
            if count > 1:
                total_debit = sum(line.debit for line in self.line_ids if line.account_id.id == acc_id)
                total_credit = sum(line.credit for line in self.line_ids if line.account_id.id == acc_id)
                last_name = self.line_ids.filtered(lambda line: line.account_id.id == acc_id)

                name = last_name[0].name if last_name else ''

                if total_debit > 0:
                    new_lines.append((0, 0, {
                        'invoice_group_account_account_id': acc_id,
                        'invoice_group_account_label': name,
                        'invoice_group_account_debit': total_debit,
                        'invoice_group_account_credit': 0
                    }))

                if total_credit > 0:
                    new_lines.append((0, 0, {
                        'invoice_group_account_account_id': acc_id,
                        'invoice_group_account_label': name,
                        'invoice_group_account_debit': 0,
                        'invoice_group_account_credit': total_credit
                    }))
            else:
                find_account_id = self.line_ids.filtered(lambda l: l.account_id.id == acc_id)
                if find_account_id:
                    new_lines.append((0, 0, {
                        'invoice_group_account_account_id': find_account_id.account_id.id,
                        'invoice_group_account_label': find_account_id.name,
                        'invoice_group_account_debit': find_account_id.debit,
                        'invoice_group_account_credit': find_account_id.credit
                    }))

        if new_lines:
            self.write({'invoice_group_account_line_ids': new_lines})

        self.check_duplicate_group = True

    
    def action_post(self):
        res = super(AccountMove, self).action_post()
        for move in self:
            move.merge_group_line()
        return res

class InvoiceGroupAccountMoveLine(models.Model):
    _name = "invoice.group.account.move.line"
    _description = "Invoice Group Account Move Line"

    invoice_group_account_id = fields.Many2one('account.move', string='Invoice Group Account Move')

    invoice_group_account_account_id = fields.Many2one('account.account', string='Account')

    invoice_group_account_label = fields.Char(string='Label')
    invoice_group_account_company_id = fields.Many2one('res.company', store=True, copy=False, string='Company', default=lambda self: self.env.user.company_id.id)
    invoice_group_account_currency_id = fields.Many2one('res.currency', string="Currency", related="invoice_group_account_company_id.currency_id", default=lambda self: self.env.user.company_id.currency_id.id)

    invoice_group_account_debit = fields.Monetary(string="Debit", currency_field='invoice_group_account_currency_id')
    invoice_group_account_credit = fields.Monetary(string="Credit", currency_field='invoice_group_account_currency_id')

    


