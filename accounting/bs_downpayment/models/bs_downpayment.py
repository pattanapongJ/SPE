# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class BsDownpayment(models.Model):
    _name = 'bs.downpayment'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'BS Down Payment'
    _order = 'payment_date desc, id desc'
    _check_company_auto = True

    @api.model
    def _default_product_id(self):
        product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
        return self.env['product.product'].browse(int(product_id)).exists()

    name = fields.Char(string='Name', required=True, copy=False, readonly=True,
                       index=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', 'Partner', required=True, ondelete='restrict', tracking=True)
    amount = fields.Monetary('Amount', required=True, tracking=True)
    payment_date = fields.Date('Date', required=True, tracking=True)
    reference = fields.Char('Reference')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('post', 'Posted')
    ], string='Status', default='draft', tracking=True, copy=False)
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True,
                                  states={'draft': [('readonly', False)]},
                                  string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    product_id = fields.Many2one('product.product', string='Down Payment Product', required=True, tracking=True,
                                 domain="[('type','=','service'),('is_downpayment','=',True)]", default=_default_product_id)
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type',
                                    copy=True, required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company, readonly=True)

    move_ids = fields.One2many('account.move', 'bs_downpayment_id', string='Journal Entry')
    downpayment_lines = fields.One2many('bs.downpayment.line', 'downpayment_id', string='Down Payment Detail Lines')
    remaining_balance = fields.Float('Balance', compute='_compute_balance')
    has_downpayment_entry = fields.Boolean('Has Downpayment Entry', compute='_compute_has_down_payment_entry')
    has_journal_items = fields.Boolean('Has Journal Item', compute='_compute_has_journal_items')

    @api.depends('move_ids')
    def _compute_has_down_payment_entry(self):
        for record in self:
            record.has_downpayment_entry = bool(record.move_ids)

    @api.depends('downpayment_lines.move_line_id')
    def _compute_has_journal_items(self):
        for record in self:
            record.has_journal_items = bool(record.downpayment_lines.filtered(lambda x: x.move_line_id))

    @api.depends('downpayment_lines.amount', 'amount')
    def _compute_balance(self):
        for record in self:
            record.remaining_balance = record.amount - sum(
                line.amount for line in record.downpayment_lines.filtered(lambda x: x.move_id))

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            _sequence_action = self.env['ir.sequence'].next_by_code('bs.customer.downpayment') if vals[
                                                                                                      'payment_type'] == 'inbound' else \
                self.env['ir.sequence'].next_by_code('bs.vendor.downpayment')
            vals['name'] = _sequence_action or 'New'
        return super(BsDownpayment, self).create(vals)

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_create_downpayment_entry(self):
        self.ensure_one()
        vals = self._prepare_default_invoice_val()
        move = self.env['account.move'].create(vals)
        move.write({'invoice_line_ids': [(0, 0, self._prepare_default_invoice_line_val())]})
        self.action_confirm()
        return self.with_context(open_downpayment_entry=True).open_journal_entry()

    def _prepare_default_invoice_val(self):
        return {
            'move_type': 'out_invoice' if self.payment_type != 'outbound' else 'in_invoice',
            'partner_id': self.partner_id.id,
            'date': self.payment_date,
            'invoice_date': self.payment_date,
            'currency_id': self.currency_id.id,
            'bs_downpayment_id': self.id
        }

    def _prepare_default_invoice_line_val(self):
        return {
            'product_id': self.product_id.id,
            'quantity': 1,
            'product_uom_id': self.product_id.uom_id.id,
            'price_unit': self.amount,
        }

    def open_journal_entry(self):
        move_ids = self.move_ids if self._context.get('open_downpayment_entry',
                                                      False) else self.downpayment_lines.mapped('move_id')
        if self.payment_type == 'inbound':
            action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        else:
            action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_invoice_type")
        if len(move_ids) > 1:
            action['domain'] = [('id', 'in', move_ids.ids)]
        elif len(move_ids) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = move_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        return action
