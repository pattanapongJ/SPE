# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from itertools import groupby
from pytz import timezone, UTC
from werkzeug.urls import url_encode
import re
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang

class AccountMove(models.Model):
    _inherit = "account.move"

    def _recompute_tax_lines(self, recompute_tax_base_amount=False, tax_rep_lines_to_recompute=None):
        """ Compute the dynamic tax lines of the journal entry.

        :param recompute_tax_base_amount: Flag forcing only the recomputation of the `tax_base_amount` field.
        """
        self.ensure_one()
        in_draft_mode = self != self._origin

        def _serialize_tax_grouping_key(grouping_dict):
            ''' Serialize the dictionary values to be used in the taxes_map.
            :param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
            :return: A string representing the values.
            '''
            return '-'.join(str(v) for v in grouping_dict.values())

        def _compute_base_line_taxes(base_line):
            ''' Compute taxes amounts both in company currency / foreign currency as the ratio between
            amount_currency & balance could not be the same as the expected currency rate.
            The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
            :param base_line:   The account.move.line owning the taxes.
            :return:            The result of the compute_all method.
            '''
            move = base_line.move_id

            if move.is_invoice(include_receipts=True):
                handle_price_include = True
                sign = -1 if move.is_inbound() else 1
                # quantity = base_line.quantity
                quantity = 1.0
                is_refund = move.move_type in ('out_refund', 'in_refund')
                price_unit_wo_discount = sign * ((base_line.price_unit * base_line.quantity) - base_line.dis_price)
            else:
                handle_price_include = False
                quantity = 1.0
                tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
                is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)
                price_unit_wo_discount = base_line.amount_currency
            balance_taxes_res = base_line.tax_ids._origin.with_context(force_sign=move._get_tax_force_sign()).compute_all(
                price_unit_wo_discount,
                currency=base_line.currency_id,
                quantity=quantity,
                product=base_line.product_id,
                partner=base_line.partner_id,
                is_refund=is_refund,
                handle_price_include=handle_price_include,
            )

            if move.move_type == 'entry':
                repartition_field = is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids'
                repartition_tags = base_line.tax_ids.flatten_taxes_hierarchy().mapped(repartition_field).filtered(lambda x: x.repartition_type == 'base').tag_ids
                tags_need_inversion = self._tax_tags_need_inversion(move, is_refund, tax_type)
                if tags_need_inversion:
                    balance_taxes_res['base_tags'] = base_line._revert_signed_tags(repartition_tags).ids
                    for tax_res in balance_taxes_res['taxes']:
                        tax_res['tag_ids'] = base_line._revert_signed_tags(self.env['account.account.tag'].browse(tax_res['tag_ids'])).ids

            return balance_taxes_res

        taxes_map = {}

        # ==== Add tax lines ====
        to_remove = self.env['account.move.line']
        for line in self.line_ids.filtered('tax_repartition_line_id'):
            grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
            grouping_key = _serialize_tax_grouping_key(grouping_dict)
            if grouping_key in taxes_map:
                # A line with the same key does already exist, we only need one
                # to modify it; we have to drop this one.
                to_remove += line
            else:
                taxes_map[grouping_key] = {
                    'tax_line': line,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                }
        if not recompute_tax_base_amount:
            self.line_ids -= to_remove

        # ==== Mount base lines ====
        for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
            # Don't call compute_all if there is no tax.
            if not line.tax_ids:
                if not recompute_tax_base_amount:
                    line.tax_tag_ids = [(5, 0, 0)]
                continue

            compute_all_vals = _compute_base_line_taxes(line)

            # Assign tags on base line
            if not recompute_tax_base_amount:
                line.tax_tag_ids = compute_all_vals['base_tags'] or [(5, 0, 0)]

            tax_exigible = True
            for tax_vals in compute_all_vals['taxes']:
                grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
                grouping_key = _serialize_tax_grouping_key(grouping_dict)

                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_vals['tax_repartition_line_id'])
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

                if tax.tax_exigibility == 'on_payment':
                    tax_exigible = False

                taxes_map_entry = taxes_map.setdefault(grouping_key, {
                    'tax_line': None,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                })
                taxes_map_entry['amount'] += tax_vals['amount']
                taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'], tax_repartition_line, tax_vals['group'])
                taxes_map_entry['grouping_dict'] = grouping_dict
            if not recompute_tax_base_amount:
                line.tax_exigible = tax_exigible

        # ==== Pre-process taxes_map ====
        taxes_map = self._preprocess_taxes_map(taxes_map)

        # ==== Process taxes_map ====
        for taxes_map_entry in taxes_map.values():
            # The tax line is no longer used in any base lines, drop it.
            if taxes_map_entry['tax_line'] and not taxes_map_entry['grouping_dict']:
                if not recompute_tax_base_amount:
                    self.line_ids -= taxes_map_entry['tax_line']
                continue

            currency = self.env['res.currency'].browse(taxes_map_entry['grouping_dict']['currency_id'])

            # Don't create tax lines with zero balance.
            if currency.is_zero(taxes_map_entry['amount']):
                if taxes_map_entry['tax_line'] and not recompute_tax_base_amount:
                    self.line_ids -= taxes_map_entry['tax_line']
                continue

            # tax_base_amount field is expressed using the company currency.
            tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id, self.company_id, self.date or fields.Date.context_today(self))

            # Recompute only the tax_base_amount.
            if recompute_tax_base_amount:
                if taxes_map_entry['tax_line']:
                    taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
                continue

            balance = currency._convert(
                taxes_map_entry['amount'],
                self.company_currency_id,
                self.company_id,
                self.date or fields.Date.context_today(self),
            )
            amount_currency = currency.round(taxes_map_entry['amount'])
            sign = -1 if self.is_inbound() else 1
            to_write_on_line = {
                'amount_currency': amount_currency,
                'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
                'tax_base_amount': tax_base_amount,
                'price_total': sign * amount_currency,
                'price_subtotal': sign * amount_currency,
            }

            if taxes_map_entry['tax_line']:
                # Update an existing tax line.
                if tax_rep_lines_to_recompute and taxes_map_entry['tax_line'].tax_repartition_line_id not in tax_rep_lines_to_recompute:
                    continue

                taxes_map_entry['tax_line'].update(to_write_on_line)
            else:
                # Create a new tax line.
                create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)

                if tax_rep_lines_to_recompute and tax_repartition_line not in tax_rep_lines_to_recompute:
                    continue

                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
                taxes_map_entry['tax_line'] = create_method({
                    **to_write_on_line,
                    'name': tax.name,
                    'move_id': self.id,
                    'company_id': self.company_id.id,
                    'company_currency_id': self.company_currency_id.id,
                    'tax_base_amount': tax_base_amount,
                    'exclude_from_invoice_tab': True,
                    'tax_exigible': tax.tax_exigibility == 'on_invoice',
                    **taxes_map_entry['grouping_dict'],
                })

            if in_draft_mode:
                taxes_map_entry['tax_line'].update(taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))

    


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    triple_discount = fields.Char('Discount',)
    dis_price = fields.Float('Discount price',digits=(16,2), compute='_compute_amount')

    def _apply_triple_discount(self, price_total,quantity):
        self.ensure_one()
        discounts = self.triple_discount.replace(" ", "").split("+")
        total_dis = 0.0
        for dis in discounts:
            if dis.endswith("%"):
                dis_percen = dis.replace("%", "")
                total_percen = (price_total * float(dis_percen)) / 100
                price_total -= total_percen
            else:
                total_baht = float(dis) * quantity
                price_total -= total_baht
        return price_total


    def _get_price_total_and_subtotal(self, price_unit=None, quantity=None, discount=None, currency=None, product=None, partner=None, taxes=None, move_type=None):
        self.ensure_one()
        return self._get_price_total_and_subtotal_model(
            price_unit=self.price_unit if price_unit is None else price_unit,
            quantity=self.quantity if quantity is None else quantity,
            discount=self.dis_price if discount is None else discount,
            currency=self.currency_id if currency is None else currency,
            product=self.product_id if product is None else product,
            partner=self.partner_id if partner is None else partner,
            taxes=self.tax_ids if taxes is None else taxes,
            move_type=self.move_id.move_type if move_type is None else move_type,
        )
    
    def _get_fields_onchange_balance(self, quantity=None, discount=None, amount_currency=None, move_type=None, currency=None, taxes=None, price_subtotal=None, force_computation=False):
        self.ensure_one()
        return self._get_fields_onchange_balance_model(
            quantity=self.quantity if quantity is None else quantity,
            discount=self.dis_price if discount is None else discount,
            amount_currency=self.amount_currency if amount_currency is None else amount_currency,
            move_type=self.move_id.move_type if move_type is None else move_type,
            currency=(self.currency_id or self.move_id.currency_id) if currency is None else currency,
            taxes=self.tax_ids if taxes is None else taxes,
            price_subtotal=self.price_subtotal if price_subtotal is None else price_subtotal,
            force_computation=force_computation,
        )
    
    @api.depends('triple_discount','quantity','price_unit')
    def _compute_amount(self):
        for line in self:
            total_dis = 0.0
            price_total = line.price_unit * line.quantity
            if line.triple_discount:
                try:
                    discounts = line.triple_discount.replace(" ", "").split("+")
                    pattern = re.compile(r'^\d+(\.\d+)?%$|^\d+(\.\d+)?$')

                    for discount in discounts:
                        if not pattern.match(discount):
                            raise ValidationError(_('Invalid Discount format : 20%+100'))

                    for dis in discounts:
                        if dis.endswith("%"):
                            dis_percen = dis.replace("%", "")
                            total_percen = ((price_total) * float(dis_percen)) / 100
                            price_total -= total_percen
                            total_dis += total_percen
                        else:
                            total_baht = float(dis)
                            price_total -= total_baht
                            total_dis += total_baht
                except:
                    raise ValidationError(_('Invalid Discount format : 20%+100'))
            line.dis_price = total_dis
            line.update(line._get_price_total_and_subtotal())
    def write(self, vals):
        # OVERRIDE
        ACCOUNTING_FIELDS = ('debit', 'credit', 'amount_currency')
        BUSINESS_FIELDS = ('price_unit', 'quantity', 'discount', 'tax_ids','triple_discount')
        PROTECTED_FIELDS_TAX_LOCK_DATE = ['debit', 'credit', 'tax_line_id', 'tax_ids', 'tax_tag_ids']
        PROTECTED_FIELDS_LOCK_DATE = PROTECTED_FIELDS_TAX_LOCK_DATE + ['account_id', 'journal_id', 'amount_currency', 'currency_id', 'partner_id']
        PROTECTED_FIELDS_RECONCILIATION = ('account_id', 'date', 'debit', 'credit', 'amount_currency', 'currency_id')

        account_to_write = self.env['account.account'].browse(vals['account_id']) if 'account_id' in vals else None

        # Check writing a deprecated account.
        if account_to_write and account_to_write.deprecated:
            raise UserError(_('You cannot use a deprecated account.'))

        inalterable_fields = set(self._get_integrity_hash_fields()).union({'inalterable_hash', 'secure_sequence_number'})
        hashed_moves = self.move_id.filtered('inalterable_hash')
        violated_fields = set(vals) & inalterable_fields
        if hashed_moves and violated_fields:
            raise UserError(_(
                "You cannot edit the following fields: %s.\n"
                "The following entries are already hashed:\n%s",
                ', '.join(f['string'] for f in self.fields_get(violated_fields).values()),
                '\n'.join(hashed_moves.mapped('name')),
            ))
        for line in self:
            if line.parent_state == 'posted':
                if any(key in vals for key in ('tax_ids', 'tax_line_id')):
                    raise UserError(_('You cannot modify the taxes related to a posted journal item, you should reset the journal entry to draft to do so.'))

            # Check the lock date.
            if any(self.env['account.move']._field_will_change(line, vals, field_name) for field_name in PROTECTED_FIELDS_LOCK_DATE):
                line.move_id._check_fiscalyear_lock_date()

            # Check the tax lock date.
            if any(self.env['account.move']._field_will_change(line, vals, field_name) for field_name in PROTECTED_FIELDS_TAX_LOCK_DATE):
                line._check_tax_lock_date()

            # Check the reconciliation.
            if any(self.env['account.move']._field_will_change(line, vals, field_name) for field_name in PROTECTED_FIELDS_RECONCILIATION):
                line._check_reconciliation()

            # Check switching receivable / payable accounts.
            if account_to_write:
                account_type = line.account_id.user_type_id.type
                if line.move_id.is_sale_document(include_receipts=True):
                    if (account_type == 'receivable' and account_to_write.user_type_id.type != account_type) \
                            or (account_type != 'receivable' and account_to_write.user_type_id.type == 'receivable'):
                        raise UserError(_("You can only set an account having the receivable type on payment terms lines for customer invoice."))
                if line.move_id.is_purchase_document(include_receipts=True):
                    if (account_type == 'payable' and account_to_write.user_type_id.type != account_type) \
                            or (account_type != 'payable' and account_to_write.user_type_id.type == 'payable'):
                        raise UserError(_("You can only set an account having the payable type on payment terms lines for vendor bill."))

        # Tracking stuff can be skipped for perfs using tracking_disable context key
        if not self.env.context.get('tracking_disable', False):
            # Get all tracked fields (without related fields because these fields must be manage on their own model)
            tracking_fields = []
            for value in vals:
                field = self._fields[value]
                if hasattr(field, 'related') and field.related:
                    continue # We don't want to track related field.
                if hasattr(field, 'tracking') and field.tracking:
                    tracking_fields.append(value)
            ref_fields = self.env['account.move.line'].fields_get(tracking_fields)

            # Get initial values for each line
            move_initial_values = {}
            for line in self.filtered(lambda l: l.move_id.posted_before): # Only lines with posted once move.
                for field in tracking_fields:
                    # Group initial values by move_id
                    if line.move_id.id not in move_initial_values:
                        move_initial_values[line.move_id.id] = {}
                    move_initial_values[line.move_id.id].update({field: line[field]})

        result = True
        for line in self:
            cleaned_vals = line.move_id._cleanup_write_orm_values(line, vals)
            if not cleaned_vals:
                continue

            # Auto-fill amount_currency if working in single-currency.
            if 'currency_id' not in cleaned_vals \
                and line.currency_id == line.company_currency_id \
                and any(field_name in cleaned_vals for field_name in ('debit', 'credit')):
                cleaned_vals.update({
                    'amount_currency': vals.get('debit', 0.0) - vals.get('credit', 0.0),
                })

            result |= super(AccountMoveLine, line).write(cleaned_vals)

            if not line.move_id.is_invoice(include_receipts=True):
                continue

            # Ensure consistency between accounting & business fields.
            # As we can't express such synchronization as computed fields without cycling, we need to do it both
            # in onchange and in create/write. So, if something changed in accounting [resp. business] fields,
            # business [resp. accounting] fields are recomputed.
            if any(field in cleaned_vals for field in ACCOUNTING_FIELDS):
                price_subtotal = line._get_price_total_and_subtotal().get('price_subtotal', 0.0)
                to_write = line._get_fields_onchange_balance(price_subtotal=price_subtotal)
                to_write.update(line._get_price_total_and_subtotal(
                    price_unit=to_write.get('price_unit', line.price_unit),
                    quantity=to_write.get('quantity', line.quantity),
                    discount=to_write.get('dis_price', line.dis_price),
                ))
                result |= super(AccountMoveLine, line).write(to_write)
            elif any(field in cleaned_vals for field in BUSINESS_FIELDS):
                to_write = line._get_price_total_and_subtotal()
                to_write.update(line._get_fields_onchange_subtotal(
                    price_subtotal=to_write['price_subtotal'],
                ))
                result |= super(AccountMoveLine, line).write(to_write)

        # Check total_debit == total_credit in the related moves.
        if self._context.get('check_move_validity', True):
            self.mapped('move_id')._check_balanced()

        self.mapped('move_id')._synchronize_business_models({'line_ids'})

        if not self.env.context.get('tracking_disable', False):
            # Create the dict for the message post
            tracking_values = {}  # Tracking values to write in the message post
            for move_id, modified_lines in move_initial_values.items():
                tmp_move = {move_id: []}
                for line in self.filtered(lambda l: l.move_id.id == move_id):
                    changes, tracking_value_ids = line._mail_track(ref_fields, modified_lines)  # Return a tuple like (changed field, ORM command)
                    if tracking_value_ids:
                        for value in tracking_value_ids:
                            selected_field = value[2]  # Get the last element of the tuple in the list of ORM command. (changed, [(0, 0, THIS)])
                            tmp_move[move_id].append({
                                'line_id': line.id,
                                **{'field_name': selected_field.get('field_desc')},
                                **self._get_formated_values(selected_field)
                            })
                    elif changes:
                        for change in changes:
                            field_name = line._fields[change].string  # Get the field name
                            tmp_move[move_id].append({
                                'line_id': line.id,
                                'error': True,
                                'field_error': field_name,
                            })
                    else:
                        continue
                if len(tmp_move[move_id]) > 0:
                    tracking_values.update(tmp_move)

            # Write in the chatter.
            for move in self.mapped('move_id'):
                fields = tracking_values.get(move.id, [])
                if len(fields) > 0:
                    msg = self._get_tracking_field_string(tracking_values.get(move.id))
                    move.message_post(body=msg)  # Write for each concerned move the message in the chatter

        return result

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        res = {}
        price_total = price_unit * quantity

        # แก้ไขส่วนลดเพื่อรองรับฟิลด์ triple_discount
        if self.triple_discount:
            price_total = self._apply_triple_discount(price_total,quantity)

        # คำนวณราคาหลังหักส่วนลด
        subtotal = price_total

        # คำนวณ 'price_total' รวมภาษีหลังหักส่วนลดแล้ว
        if taxes:
            taxes_res = taxes._origin.with_context(force_sign=1).compute_all(price_total,
                quantity=1, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        #In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res
    

    @api.model_create_multi
    def create(self, vals_list):
        # OVERRIDE
        ACCOUNTING_FIELDS = ('debit', 'credit', 'amount_currency')
        BUSINESS_FIELDS = ('price_unit', 'quantity', 'triple_discount', 'tax_ids','discount','dis_price')

        for vals in vals_list:
            move = self.env['account.move'].browse(vals['move_id'])
            vals.setdefault('company_currency_id', move.company_id.currency_id.id) # important to bypass the ORM limitation where monetary fields are not rounded; more info in the commit message

            # Ensure balance == amount_currency in case of missing currency or same currency as the one from the
            # company.
            currency_id = vals.get('currency_id') or move.company_id.currency_id.id
            if currency_id == move.company_id.currency_id.id:
                balance = vals.get('debit', 0.0) - vals.get('credit', 0.0)
                vals.update({
                    'currency_id': currency_id,
                    'amount_currency': balance,
                })
            else:
                vals['amount_currency'] = vals.get('amount_currency', 0.0)

            if move.is_invoice(include_receipts=True):
                currency = move.currency_id
                partner = self.env['res.partner'].browse(vals.get('partner_id'))
                taxes = self.new({'tax_ids': vals.get('tax_ids', [])}).tax_ids
                tax_ids = set(taxes.ids)
                taxes = self.env['account.tax'].browse(tax_ids)

                # Ensure consistency between accounting & business fields.
                # As we can't express such synchronization as computed fields without cycling, we need to do it both
                # in onchange and in create/write. So, if something changed in accounting [resp. business] fields,
                # business [resp. accounting] fields are recomputed.
                if any(vals.get(field) for field in ACCOUNTING_FIELDS):
                    price_subtotal = self._get_price_total_and_subtotal_model(
                        vals.get('price_unit', 0.0),
                        vals.get('quantity', 0.0),
                        vals.get('dis_price', 0.0),
                        currency,
                        self.env['product.product'].browse(vals.get('product_id')),
                        partner,
                        taxes,
                        move.move_type,
                    ).get('price_subtotal', 0.0)
                    vals.update(self._get_fields_onchange_balance_model(
                        vals.get('quantity', 0.0),
                        vals.get('dis_price', 0.0),
                        vals['amount_currency'],
                        move.move_type,
                        currency,
                        taxes,
                        price_subtotal
                    ))
                    vals.update(self._get_price_total_and_subtotal_model(
                        vals.get('price_unit', 0.0),
                        vals.get('quantity', 0.0),
                        vals.get('dis_price', 0.0),
                        currency,
                        self.env['product.product'].browse(vals.get('product_id')),
                        partner,
                        taxes,
                        move.move_type,
                    ))
                elif any(vals.get(field) for field in BUSINESS_FIELDS):
                    vals.update(self._get_price_total_and_subtotal_model(
                        vals.get('price_unit', 0.0),
                        vals.get('quantity', 0.0),
                        vals.get('dis_price', 0.0),
                        currency,
                        self.env['product.product'].browse(vals.get('product_id')),
                        partner,
                        taxes,
                        move.move_type,
                    ))
                    vals.update(self._get_fields_onchange_subtotal_model(
                        vals['price_subtotal'],
                        move.move_type,
                        currency,
                        move.company_id,
                        move.date,
                    ))

        lines = super(AccountMoveLine, self).create(vals_list)

        moves = lines.mapped('move_id')
        if self._context.get('check_move_validity', True):
            moves._check_balanced()
        moves._check_fiscalyear_lock_date()
        lines._check_tax_lock_date()
        moves._synchronize_business_models({'line_ids'})

        return lines

    @api.model
    def _get_fields_onchange_balance_model(self, quantity, discount, amount_currency, move_type, currency, taxes, price_subtotal, force_computation=False):
        ''' This method is used to recompute the values of 'quantity', 'discount', 'price_unit' due to a change made
        in some accounting fields such as 'balance'.

        This method is a bit complex as we need to handle some special cases.
        For example, setting a positive balance with a 100% discount.

        :param quantity:        The current quantity.
        :param discount:        The current discount.
        :param amount_currency: The new balance in line's currency.
        :param move_type:       The type of the move.
        :param currency:        The currency.
        :param taxes:           The applied taxes.
        :param price_subtotal:  The price_subtotal.
        :return:                A dictionary containing 'quantity', 'discount', 'price_unit'.
        '''
        if move_type in self.move_id.get_outbound_types():
            sign = 1
        elif move_type in self.move_id.get_inbound_types():
            sign = -1
        else:
            sign = 1
        amount_currency *= sign

        # Avoid rounding issue when dealing with price included taxes. For example, when the price_unit is 2300.0 and
        # a 5.5% price included tax is applied on it, a balance of 2300.0 / 1.055 = 2180.094 ~ 2180.09 is computed.
        # However, when triggering the inverse, 2180.09 + (2180.09 * 0.055) = 2180.09 + 119.90 = 2299.99 is computed.
        # To avoid that, set the price_subtotal at the balance if the difference between them looks like a rounding
        # issue.
        if not force_computation and currency.is_zero(amount_currency - price_subtotal):
            return {}

        taxes = taxes.flatten_taxes_hierarchy()
        if taxes and any(tax.price_include for tax in taxes):
            # Inverse taxes. E.g:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 110           | 10% incl, 5%  |                   | 100               | 115
            # 10            |               | 10% incl          | 10                | 10
            # 5             |               | 5%                | 5                 | 5
            #
            # When setting the balance to -200, the expected result is:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 220           | 10% incl, 5%  |                   | 200               | 230
            # 20            |               | 10% incl          | 20                | 20
            # 10            |               | 5%                | 10                | 10
            force_sign = -1 if move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1
            taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(amount_currency, currency=currency, handle_price_include=False)
            for tax_res in taxes_res['taxes']:
                tax = self.env['account.tax'].browse(tax_res['id'])
                if tax.price_include:
                    amount_currency += tax_res['amount']

        discount_factor = False
        if discount :
            discount_factor = discount 
        if amount_currency and discount_factor:
            # discount != 100%
            vals = {
                'quantity': quantity or 1.0,
                # 'price_unit': (amount_currency - discount_factor) * (quantity or 1.0),
                'price_subtotal': (amount_currency - discount_factor) * (quantity or 1.0),
            }
        elif amount_currency and not discount_factor:
            # discount == 100%
            vals = {
                'quantity': quantity or 1.0,
                'discount': 0.0,
                # 'price_unit': amount_currency / (quantity or 1.0),
            }
        elif not discount_factor:
            # balance of line is 0, but discount  == 100% so we display the normal unit_price
            vals = {}
        else:
            # balance is 0, so unit price is 0 as well
            vals = {'price_unit': 0.0}
        return vals
    
    @api.onchange('quantity', 'dis_price', 'price_unit', 'tax_ids','triple_discount')
    def _onchange_price_subtotal(self):
        for line in self:
            if not line.move_id.is_invoice(include_receipts=True):
                continue

            line.update(line._get_price_total_and_subtotal())
            line.update(line._get_fields_onchange_subtotal())

