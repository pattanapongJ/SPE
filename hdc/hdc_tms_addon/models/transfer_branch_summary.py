# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta

class ReSupplyTransferBranchSummary(models.Model):
    _inherit = "resupply.transfer.branch.summary"

    company_id = fields.Many2one("res.company", string = "Company", default=lambda self: self.env.company)
    delivery_resend = fields.Boolean('Delivery Resend')
    note_type = fields.Selection(
        [
            ('tms', 'TMS Normal'),
            ('credit', 'Credit Note'),
            ('debit', 'Debit Note'),
            ('cancel', 'Invoice Cancel'),
        ],
        string="Filter Note Type",
        default='tms'
    )

    spe_invoice = fields.Many2one(
        'account.move',
        string="SPE Invoice",
    )
    invoice_date = fields.Date(string="Invoice Date")

    filter_credit_note_ids = fields.Many2many(
        comodel_name='account.move', 
        relation='resupply_transfer_branch_summary_credit_note_rel',
        column1='resupply_transfer_branch_summary_id',
        column2='account_move_id',
        string='Credit Note', 
        domain=[('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('is_tms', '=', False)]
    )
    filter_debit_note_ids = fields.Many2many(
        comodel_name='account.move', 
        relation='resupply_transfer_branch_summary_debit_note_rel',
        column1='resupply_transfer_branch_summary_id',
        column2='account_move_id',
        string='Debit Note', 
        domain=[('move_type', '=', 'in_refund'), ('state', '=', 'posted'), ('is_tms', '=', False)]
    )
    filter_invoice_cancel_ids = fields.Many2many(
        comodel_name='account.move', 
        relation='resupply_transfer_branch_summary_invoice_cancel_rel',
        column1='resupply_transfer_branch_summary_id',
        column2='account_move_id',
        string='Invoice Cancel', 
        domain=[('state', '=', 'cancel'), ('move_type', '=', 'out_invoice'), ('is_tms', '=', False)]
    )

    def search_action(self):
        domain_search = [
            ('is_tms', '=', False),
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice'),
            '|',
                ('delivery_status', '!=', 'completed'),
                '|',  # เพิ่มอีก OR ชุดใหม่
                    '&',
                        ('delivery_status', '=', 'completed'),
                        ('billing_status', '=', 'none'),
                    '&',
                        ('billing_status', 'in', ['to_finance', 'to_billing']),
                        ('to_finance', '=', False),
        ]


        
        if self.note_type in ['credit', 'debit', 'cancel']:
            return self._search_note_type_invoice()

        if self.scheduled_date_start:
            if self.scheduled_date_end and self.scheduled_date_end < self.scheduled_date_start:
                raise UserError(_("The end date cannot be less than the start date."))
            datetime_start = (self.scheduled_date_start - relativedelta(days=1)).strftime("%Y-%m-%d 17:00:00")
            domain_search += [('invoice_date', '>=', datetime_start)]
        
        if self.scheduled_date_end:
            datetime_end = self.scheduled_date_end.strftime("%Y-%m-%d 16:59:59")
            domain_search += [('invoice_date', '<=', datetime_end)]
        if self.spe_invoice_ids:
            domain_search += [('id', 'in', self.spe_invoice_ids.ids)]
        if self.invoice_ids:
            if self.delivery_resend:
                domain_search = ['|',('resend_status', '=', 'Resend'),('id', 'in', self.invoice_ids.ids)]
            else:
                domain_search += [('id', 'in', self.invoice_ids.ids)]
        else:
            if self.delivery_resend:
                domain_search += [('resend_status', '=', 'Resend')]

        if self.transport_line_ids:
            domain_search += [('transport_line_id', 'in', self.transport_line_ids.ids)]
        
        if self.company_round_ids:
            domain_search += [('company_round_id', 'in', self.company_round_ids.ids)]

        
        source = []
        if self.sale_order_ids:
            for order_id in self.sale_order_ids:
                if order_id.name not in source:
                    source += [order_id.name]

        if self.delivery_order_ids:
            for order_id in self.delivery_order_ids:
                if order_id.origin not in source:
                    source += [order_id.origin]
        if self.partner_ids:
            partner_ids = []
            for partner_id in self.partner_ids:
                # เพิ่ม partner หลัก
                partner_ids.append(partner_id.id)
                # เพิ่ม child partners (branches, contacts, etc.)
                child_partners = self.env['res.partner'].search([('parent_id', '=', partner_id.id)])
                if child_partners:
                    partner_ids.extend(child_partners.ids)

            domain_search += [('partner_id', 'in', partner_ids)]
        
        if len(source) > 0:
            domain_search += [('invoice_origin', 'in', source)]
        transfer_search_config = self.env['account.move'].search(domain_search + [])
        self.invoice_line_ids.unlink()

        order_line = []
        for transfer in transfer_search_config:
            delivery_id = False
            if transfer.invoice_origin:
                sale_id = self.env['sale.order'].search([("name", "=", transfer.invoice_origin)])
                delivery_id = sale_id.picking_ids[-1] if sale_id.picking_ids else False

            line = (0, 0, {
                'search_id': self.id,
                'delivery_date': transfer.invoice_date,
                'invoice_id': transfer.id,
                'partner_id': transfer.partner_id.id,
                'delivery_address_id': transfer.partner_shipping_id.id,
                'transport_line_id': transfer.transport_line_id.id,
                'company_round_id': transfer.company_round_id.id,
                'sale_no': transfer.invoice_origin,
                'delivery_id': delivery_id.id if delivery_id else False,
                'sale_person': transfer.invoice_user_id.id,
                'resend_status': transfer.resend_status,
                'status': transfer.state,
            })
            order_line.append(line)

        self.write({
            'invoice_line_ids': order_line
        })

    def _search_note_type_invoice(self):
        self.ensure_one()
        domain = [
            ('is_tms', '=', False), 
            ('delivery_status', 'not in', ['cancel'])
        ]

        if self.note_type == 'credit':
            domain.append(('move_type', '=', 'out_refund'))
            domain.append(('state', '=', 'posted'))
            if self.filter_credit_note_ids:
                domain.append(('id', 'in', self.filter_credit_note_ids.ids))

        elif self.note_type == 'debit':
            domain.append(('move_type', '=', 'in_refund'))
            domain.append(('state', '=', 'posted'))
            if self.filter_debit_note_ids:
                domain.append(('id', 'in', self.filter_debit_note_ids.ids))

        elif self.note_type == 'cancel':
            domain.append(('move_type', '=', 'out_invoice'))
            domain.append(('state', '=', 'cancel'))
            if self.filter_invoice_cancel_ids:
                domain.append(('id', 'in', self.filter_invoice_cancel_ids.ids))
        
        else:
            domain.append(('move_type', '=', 'out_invoice'))
            domain.append(('state', '=', 'posted'))
            if self.filter_credit_note_ids or self.filter_debit_note_ids or self.filter_invoice_cancel_ids:
                domain.append(('id', 'not in', (
                    self.filter_credit_note_ids.ids +
                    self.filter_debit_note_ids.ids +
                    self.filter_invoice_cancel_ids.ids
                )))

        if self.invoice_date:
            domain.append(('invoice_date', '=', self.invoice_date))
        if self.spe_invoice:
            domain.append(('spe_invoice', '=', self.spe_invoice))

        transfer_search_config = self.env['account.move'].search(domain)
        self.invoice_line_ids.unlink()

        order_line = []
        for transfer in transfer_search_config:
            delivery_id = False
            if transfer.invoice_origin:
                sale_id = self.env['sale.order'].search([("name", "=", transfer.invoice_origin)])
                delivery_id = sale_id.picking_ids[-1] if sale_id.picking_ids else False

            line = (0, 0, {
                'search_id': self.id,
                'delivery_date': transfer.invoice_date,
                'invoice_id': transfer.id,
                'partner_id': transfer.partner_id.id,
                'delivery_address_id': transfer.partner_shipping_id.id,
                'transport_line_id': transfer.transport_line_id.id,
                'company_round_id': transfer.company_round_id.id,
                'sale_no': transfer.invoice_origin,
                'delivery_id': delivery_id.id if delivery_id else False,
                'sale_person': transfer.invoice_user_id.id,
                'resend_status': transfer.resend_status,
                'status': transfer.state,
            })
            order_line.append(line)

        self.write({'invoice_line_ids': order_line})
    
    def clear_all_action(self):
        # self.scheduled_date_start = False
        # self.scheduled_date_end = False
        self.operation_type_id = False
        self.invoice_ids = False
        self.spe_invoice_ids = False
        self.sale_order_ids = False
        self.delivery_order_ids = False
        self.transport_line_ids = False
        self.company_round_ids = False
        self.invoice_line_ids.unlink()
        self.delivery_resend = False
        self.filter_credit_note_ids = False
        self.filter_debit_note_ids = False
        self.filter_invoice_cancel_ids = False

    def create_delivery_noted_action(self):
        if self.invoice_line_ids:
            return {
                'name': "Cofirm Delivery Noted",
                'view_mode': 'form',
                'res_model': 'wizard.confirm.delivery.noted',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {
                    'default_search_id': self.id,
                    'default_company_id': self.company_id.ids,
                    'default_transport_line_id': self.invoice_line_ids[-1].transport_line_id.id,
                    'default_company_round_id': self.invoice_line_ids[-1].company_round_id.id,
                }
            }
    
    @api.onchange('note_type')
    def _onchange_note_type(self):
        domain = []

        if self.note_type == 'credit':
            domain = [('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('is_tms', '=', False)]
        elif self.note_type == 'debit':
            domain = [('move_type', '=', 'in_refund'), ('state', '=', 'posted'), ('is_tms', '=', False)]
        elif self.note_type == 'cancel':
            domain = [('state', '=', 'cancel'), ('move_type', '=', 'out_invoice'), ('is_tms', '=', False)]
        else:  # invoice ปกติ
            domain = [('move_type', '=', 'out_invoice'), ('state', '=', 'posted'), ('is_tms', '=', False)]

        return {
            'domain': {
                'spe_invoice': domain
            }
        }
    
class SearchInvoiceLine(models.Model):
    _inherit = "search.invoice.line"
    
    resend_status = fields.Char(string="Delivery Status")
    company_id = fields.Many2one(related='invoice_id.company_id', string="Company")

