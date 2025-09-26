# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang
from collections import defaultdict

class AccountMove(models.Model):
    _inherit = "account.move"

    rounding_untax = fields.Char(string='Rounding Untaxed Amount')
    rounding_taxes = fields.Char(string='Rounding Taxes')
    rounding_total = fields.Char(string='Rounding Total')

    def action_rounding_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Change Total Rounding',
            'view_mode': 'form',
            'res_model': 'wizard.account.change.total',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_rounding_untax': self.rounding_untax,
                'default_rounding_taxes': self.rounding_taxes,
                'default_rounding_total': self.rounding_total,
            },
        }
    
    @api.depends('rounding_untax', 'rounding_taxes', 'rounding_total')
    def _compute_amount(self):
        super(AccountMove, self)._compute_amount()
        for rec in self:
            if rec.rounding_untax:
                rounding_untax = float(rec.rounding_untax[1:])
                rec.amount_untaxed += rounding_untax if rec.rounding_untax.startswith("+") else -rounding_untax
            
            if rec.rounding_total:
                rounding_total = float(rec.rounding_total[1:])
                rec.amount_total += rounding_total if rec.rounding_total.startswith("+") else -rounding_total

    @api.depends('line_ids.price_subtotal', 'line_ids.tax_base_amount', 'line_ids.tax_line_id', 'partner_id', 'currency_id','rounding_taxes')
    def _compute_invoice_taxes_by_group(self):
        super(AccountMove, self)._compute_invoice_taxes_by_group()
        for move in self:
            if move.rounding_taxes:
                rounding_taxes = float(move.rounding_taxes[1:])
                updated_amount_by_group = []
                for group in move.amount_by_group:
                    # Assuming group[1] is the tax amount and group[3] is the formatted amount with currency symbol
                    new_tax_amount = group[1] + (rounding_taxes if move.rounding_taxes.startswith("+") else -rounding_taxes)
                    
                    # Extract numeric part of group[3] (e.g., '3,336.4486\xa0฿')
                    amount_str = group[3].replace("\xa0", " ").split(" ")[0].replace(",", "")
                    formatted_currency = group[3][-1]  # Assuming the last character is the currency symbol
                    
                    # Convert to float, adjust, and format it back
                    formatted_amount = "{:,.4f}".format(float(amount_str) + (rounding_taxes if move.rounding_taxes.startswith("+") else -rounding_taxes))

                    # Append updated data
                    updated_amount_by_group.append(
                        (group[0], new_tax_amount, group[2], f"{formatted_amount} {formatted_currency}", group[4], group[5], group[6])
                    )
                move.update({'amount_by_group': updated_amount_by_group})

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
            if base_line.rounding_price:
                rounding_value = float(base_line.rounding_price[1:])
                if base_line.rounding_price.startswith("+"):
                    price_unit_wo_discount += sign * rounding_value
                elif base_line.rounding_price.startswith("-"):
                    price_unit_wo_discount -= sign * rounding_value

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

    rounding_price = fields.Char('Rounding')

    @api.onchange('rounding_price')
    def _onchange_rounding_price(self):
        if self.rounding_price:
            decimal_precision = self.env['decimal.precision'].precision_get('Invoice Rounding')
            rounding_pattern = re.compile(r'^[+-]?\d+(\.\d{1,%d})?$' % decimal_precision)
            
            if not rounding_pattern.match(self.rounding_price):
                self.rounding_price = False
                raise ValidationError(_('Invalid Rounding format : +20 or -20 with up to %d decimal places' % decimal_precision))
    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        res = {}
        price_total = price_unit * quantity

        # แก้ไขส่วนลดเพื่อรองรับฟิลด์ triple_discount
        if self.triple_discount:
            price_total = self._apply_triple_discount(price_total,quantity)

        # คำนวณราคาหลังหักส่วนลด
        subtotal = price_total

        
        if self.rounding_price:
            rounding_value = float(self.rounding_price[1:])
            if self.rounding_price.startswith("+"):
                subtotal += rounding_value
            elif self.rounding_price.startswith("-"):
                subtotal -= rounding_value
        if taxes:
            taxes_res = taxes._origin.with_context(force_sign=1).compute_all(subtotal,
                quantity=1, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        #In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res
