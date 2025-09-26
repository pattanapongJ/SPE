# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import date, datetime
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from collections import defaultdict
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero

class ReceiptList(models.Model):
    _name = 'receipt.list'
    _description = "Receipt List"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    def _default_account_journal_id(self):
        """Take the journal configured in the company, else fallback on the stock journal."""
        lc_journal = self.env['account.journal']
        if self.env.company.lc_journal_id:
            lc_journal = self.env.company.lc_journal_id
        else:
            lc_journal = self.env['ir.property']._get("property_stock_journal", "product.category")
        return lc_journal

    name = fields.Char(string="Name", required=True, default="New", readonly=True)
    state = fields.Selection([
        ('draft', 'Prepare RL'),
        ('ready', 'Ready for Receipt'),
        ('waiting', 'Waiting Validate'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='Status', default='draft', readonly=True)

    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    user_em_id = fields.Many2one('hr.employee', string='Responsible', readonly=True)
    operation_type = fields.Many2one('stock.picking.type', string='Operation Type', domain= [('code', '=', 'incoming')])
    purchase_type = fields.Many2one('purchase.order.type', string='PO Type', required=True, domain= [('is_in_out', '=', True)])
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', readonly=True)
    location_id = fields.Many2one('stock.location', string='Location')
    company_id = fields.Many2one("res.company", string="Company", required=True, readonly=True)

    scheduled_date = fields.Datetime(string='Scheduled Date')
    receipted_date = fields.Datetime(string='Receipted Date(Backed Date)')

    performa_invoice = fields.Char(string='Performa Invoice(PI)', copy=False)
    per_invoice_date = fields.Date(string='Performa Invoice Date')
    commercial_invoice = fields.Char(string='Commercial Invoice(CI)', copy=False)
    com_invoice_date = fields.Date(string='Commercial Invoice Date')
    vendor_ref = fields.Char(string='Vendor Reference')
    po_ref = fields.Char(string='PO Reference')

    batch_ref = fields.Char(string='Batch Ref')
    currency_id = fields.Many2one('res.currency', string='Currency', domain=[('rate_type','=', 'sell')])
    exchange_date = fields.Date(string='Exchange Date')
    exchange_rate = fields.Float(string='Exchange Rate', readonly=True)
    exchange_date_free = fields.Date(string='Exchange Date(Free on Board)')
    exchange_rate_free  = fields.Float(string='Exchange Rate')

    confirmed_warehouse_date = fields.Datetime(string='Confirmed Warehouse Date')
    confirmed_warehouse_by = fields.Many2one('hr.employee', string='Confirmed Warehouse By')
    warehouse_status = fields.Selection([
        ('draft', 'In progress'),
        ('waiting', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ],string='Warehouse Status', readonly=True, default="draft")
    validate_inventory_date = fields.Datetime(string='Validate Inventory Date')
    validate_inventory_by = fields.Many2one('hr.employee', string='Validate Inventory By')
    inventory_status = fields.Selection([
        ('draft', 'In progress'),
        ('waiting', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='Inventory Status', readonly=True, default="waiting")

    shipping_provider = fields.Many2one('res.partner', string='Shipping Provider', domain=[('supplier','=', True)])
    original_country = fields.Many2one("res.country", string='Original Country')
    incoterm_id = fields.Many2one("account.incoterms", string="Incoterm")
    delivery_mode = fields.Many2one("delivery.carrier", string='Delivery Mode')
    etd = fields.Date(string='ETD')
    eta = fields.Date(string='ETA')
    rl_reference = fields.Char(string='RL Reference', copy=False)
    old_invoice_ref = fields.Char(string='Old Invoice Reference', copy=False)

    remarks = fields.Text(string='Remarks')

    invoice_no = fields.Char(string='Invoice No', copy=False)
    invoice_date_in = fields.Date(string='Invoice Date')

    external_remarks = fields.Text(string='External Remarks')
    internal_remarks = fields.Text(string='Internal Remarks')

    line_ids = fields.One2many('receipt.list.line', 'receipt_list_id', string='Lines')

    untaxed_amount = fields.Float(string='Untaxed', compute='_compute_amount')
    vat_amount = fields.Float(string='Vat', compute='_compute_amount')
    total_amount = fields.Float(string='Total', compute='_compute_amount')

    account_journal_id = fields.Many2one(
        'account.journal', 'Account Journal',
         states={'done': [('readonly', True)]}, default=lambda self: self._default_account_journal_id())
    cost_lines = fields.One2many(
        'stock.landed.cost.lines', 'receipt_list_id', 'Cost Lines',
        copy=True, states={'done': [('readonly', True)]})
    
    valuation_adjustment_lines = fields.One2many(
        'stock.valuation.adjustment.lines', 'receipt_list_id', 'Valuation Adjustments',
        states={'done': [('readonly', True)]})
    
    is_oversea = fields.Boolean(related="operation_type.is_oversea", string="is oversea")

    move_line_id = fields.Many2many('stock.move.line', string='Detail Transfer', compute="_compute_move_line")

    # item service PO
    line_service_ids = fields.One2many(
        'receipt.list.line.service', 'receipt_list_id', 'Service Lists')
    
    bills_count = fields.Float(string='Bills', compute='_compute_bills_count')

    invoice_status = fields.Selection([
        ('no', 'Nothing to Bill'),
        ('to invoice', 'Waiting Bills'),
        ('invoiced', 'Fully Billed'),
    ], string='Billing Status', compute='_get_invoiced', store=True, readonly=True, copy=False, default='no')

    shipper = fields.Char(string='Shipper',)

    def name_get(self):
        result = []
        for rec in self:
            old_invoice_ref = ''
            if rec.is_oversea:
                old_invoice_ref = rec.commercial_invoice
            else:
                old_invoice_ref = rec.invoice_no

            if old_invoice_ref:
                name = '%s (%s)' %(rec.name,old_invoice_ref)
            else:
                name = rec.name
            result.append((rec.id, name))
        return result

    @api.depends('state', 'line_ids.qty_to_invoice')
    def _get_invoiced(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for order in self:
            if order.state not in ('done'):
                order.invoice_status = 'no'
                continue

            if any(
                not float_is_zero(line.qty_to_invoice, precision_digits=precision)
                for line in order.line_ids
            ):
                order.invoice_status = 'to invoice'
            elif (
                all(
                    float_is_zero(line.qty_to_invoice, precision_digits=precision)
                    for line in order.line_ids
                )
                and order.bills_count > 0
            ):
                order.invoice_status = 'invoiced'
            else:
                order.invoice_status = 'no'

    @api.constrains('invoice_no', 'performa_invoice', 'commercial_invoice', 'partner_id')
    def _check_unique_invoice_partner(self):
        for record in self:
            if record.partner_id:
                fields_to_check = [
                    ('invoice_no', 'Invoice No'),
                    ('performa_invoice', 'Performa Invoice'),
                    ('commercial_invoice', 'Commercial Invoice')
                ]
                for field_name, field_label in fields_to_check:
                    field_value = getattr(record, field_name)
                    if field_value:
                        existing = self.search([
                            (field_name, '=', field_value),
                            ('partner_id', '=', record.partner_id.id),
                            ('id', '!=', record.id)
                        ])
                        if existing:
                            raise ValidationError(f'มีหมายเลข {field_label} เจ้าหนี้บนระบบแล้ว กรุณาตรวจสอบอีกครั้ง')

    def _compute_bills_count(self):
        for rec in self:
            account = self.env['account.move']
            for line in rec.line_ids:
                account |= line.invoice_lines.move_id
            rec.bills_count = len(account)

    def open_invoice_view(self):
        account = self.env['account.move']
        for line in self.line_ids:
            account += line.invoice_lines.move_id
        return {
            'name': _('Bills'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', account.ids)],
            'context': "{'create': False}"
        }

    def _compute_move_line(self):
        for record in self:
            move_line_id = self.env['stock.move.line']
            for rec in record.line_ids:
                    move_line_id += rec.move_id.move_line_nosuggest_ids
            record.move_line_id = move_line_id

    def _compute_amount(self):
        for record in self:
            record.untaxed_amount = sum(record.line_ids.mapped('subtotal'))
            record.vat_amount = sum(record.line_ids.mapped('price_tax'))
            record.total_amount = sum(record.line_ids.mapped('net_price'))

    @api.onchange('operation_type')
    def _onchange_operation_type(self):
        if self.operation_type:
            self.location_id = self.operation_type.default_location_dest_id.id
            self.warehouse_id = self.operation_type.warehouse_id.id


    @api.onchange('receipted_date')
    def _onchange_receipted_date(self):
        if self.receipted_date:
            self.confirmed_warehouse_date = self.receipted_date
            self.validate_inventory_date = self.receipted_date
            self.exchange_date = self.receipted_date

    @api.onchange('exchange_date')
    def _onchange_exchange_date(self):
        if self.currency_id.name != 'THB':
            if self.exchange_date:
                exchange_rate = self.env['res.currency.rate'].search([
                    ('name', '=', self.exchange_date),
                    ('currency_id', '=', self.currency_id.id),
                ], limit=1).inverse_company_rate

                if exchange_rate:
                    self.exchange_rate = exchange_rate
                else:
                    raise ValidationError("No exchange rate found for the selected date and currency.")
        else:
            self.exchange_rate = 1

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            if vals.get('purchase_type'):
                purchase_type = self.env['purchase.order.type'].search([('id', '=', vals.get('purchase_type'))])
                if purchase_type.rl_sequence_id:
                    vals['name'] = purchase_type.rl_sequence_id.next_by_id() or '/'
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code('receipt.list') or '/'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('receipt.list') or '/'
                
        return super(ReceiptList, self).create(vals)

    def cancel_close(self):
        return {
            'name': _('Cancel Receipt List'),
            'type': 'ir.actions.act_window',
            'res_model': 'cancel.receipt.list.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_receipt_list_id': self.id}
        }

    def confirm_rl(self):
        for line in self.line_ids:
            if line.shipped_qty <= 0:
                raise ValidationError("Shipped Qty is not zero.")
            line.move_id.move_line_ids.unlink()
            if line.shipped_qty < line.demand:
                origin_move = line.move_id
                copy_move = line.move_id.copy({
                        'product_uom_qty': line.shipped_qty
                    })
                line.move_id = copy_move
                origin_move.product_uom_qty = origin_move.product_uom_qty - line.shipped_qty
                line.move_id.origin_rl_move_id = origin_move.id
            line.receipt_qty = line.shipped_qty
            line.po_receipt_qty = line.po_shipped_qty
        self.state = "ready"

    def confirm_warehouse(self):
        self.confirmed_warehouse_date = datetime.now()
        self.confirmed_warehouse_by = self.search_employee()
        for line in self.line_ids:
            line.move_id.move_line_ids.unlink()
            # if line.shipped_qty < line.demand:
            #     origin_move = line.move_id
            #     copy_move = line.move_id.copy({
            #             'product_uom_qty': line.shipped_qty
            #         })
            #     line.move_id = copy_move
            #     origin_move.product_uom_qty = origin_move.product_uom_qty - line.shipped_qty
            #     line.move_id.origin_rl_move_id = origin_move.id
            line.move_id.write({'picking_type_id': self.operation_type.id,
                                'warehouse_id': self.warehouse_id.id,
                                'location_dest_id': self.operation_type.default_location_dest_id,
                                'company_id': self.warehouse_id.company_id.id})
            line._onchange_receipt_qty()
        self.state = "waiting"
        self.warehouse_status = "done"
        self.inventory_status = "draft"
    
    def confirm_inventory(self):
        for line in self.line_ids:
            if line.receipt_done <= 0:
                raise ValidationError("Receipt done Qty is not zero.")
            elif line.receipt_done > line.shipped_qty:
                raise ValidationError("Receipt done  Qty is more than Remain.")
            elif line.receipt_done < line.shipped_qty and line.receipt_done != 0:
                return  {
                            'name': _('Create Backorder'),
                            'type': 'ir.actions.act_window',
                            'res_model': 'confirm.receipt.list.wizard',
                            'view_mode': 'form',
                            'target': 'new',
                            'context': {'default_receipt_list_id': self.id}
                        }
            
        self.validate_inventory_date = datetime.now()
        self.validate_inventory_by = self.search_employee()
        self.inventory_status = "done"
        return self.confirm_validate()

    def search_employee(self):
        employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id), ("company_id", "=", self.env.user.company_id.id)], limit=1)
        if not employee_id:
            employee_id = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)], limit=1)
        return employee_id.id
    
    @api.onchange('location_id')
    def _onchange_location_id(self):
        if self.location_id and self.state == "waiting":
            for line in self.line_ids:
                line.move_id.move_line_nosuggest_ids.write({'location_dest_id': self.location_id.id,})


    def confirm_validate(self):
        backorder_move = self.env['stock.move']
        for line in self.line_ids:
            if line.move_id.picking_id.state not in ('done', 'cancel'):
                if line.receipt_done < line.shipped_qty:
                    if self.env.context.get('confirm_backorder'):
                        origin_move = line.move_id
                        copy_move = line.move_id.copy({
                                'product_uom_qty': line.shipped_qty - line.receipt_done,
                                'price_unit': line.price,
                            })
                        copy_move._action_confirm(merge=False)
                        for move_rl in origin_move.rl_move_ids:
                            if move_rl.origin_rl_move_id and move_rl.state  not in ('done', 'cancel'):
                                move_rl.origin_rl_move_id = copy_move.id
                        backorder_move += copy_move
                        origin_move.product_uom_qty = line.receipt_done
                        origin_move._action_done()
                    else:
                        if line.move_id.origin_rl_move_id.receipt_list_line_id:
                            origin_move = line.move_id
                            copy_move = line.move_id.copy({
                                    'product_uom_qty': line.shipped_qty - line.receipt_done,
                                    'price_unit': line.price,
                                })
                            copy_move._action_confirm(merge=False)
                            for move_rl in origin_move.rl_move_ids:
                                if move_rl.origin_rl_move_id and move_rl.state  not in ('done', 'cancel'):
                                    move_rl.origin_rl_move_id = copy_move.id
                            origin_move.product_uom_qty = line.receipt_done
                            origin_move._action_done()
                        else:
                            origin_move = line.move_id
                            origin_move.origin_rl_move_id.product_uom_qty += line.shipped_qty - line.receipt_done
                            origin_move.product_uom_qty = line.receipt_done
                            origin_move._action_done()
                else:
                    line.move_id._action_confirm(merge=False)
                    line.move_id._action_done()
          
        # for line in self.line_ids:
        #     if line.move_id.state != 'done':
        #         raise ValidationError("Stock move is not done.")
        self.state = "done"

        # ปิดเรื่อง cost
        # if self.cost_lines:
        #     self.cost_validate()

        if self.env.context.get('confirm_backorder') and backorder_move:
            receipt_lists = self.create_receipt_lists(backorder_move)
            return {
                'name': _('Receipt List'),
                'view_mode': 'form',
                'res_model': 'receipt.list',
                'res_id': receipt_lists.id,
                'type': 'ir.actions.act_window',
            }


    def add_items(self):
        gen_receipt_lists = self.env['gen.receipt.list'].create({
            'receipt_list_id': self.id,
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'purchase_type': self.purchase_type.id,})
        gen_receipt_lists.search_value()
        return {
            'name': _('Add : Choose Products Receipts'),
            'view_mode': 'form',
            'res_model': 'gen.receipt.list',
            'res_id': gen_receipt_lists.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_id': self.env.ref('hdc_receipt_list.add_gen_receipt_list_form_view').id
        }
    
    def create_receipt_lists(self, backorder_move):
        line_value = []
        for line in backorder_move:
            # demand = sum(self.env['stock.move'].search([('product_id', '=', line.product_id.id),('state', 'not in', ('done','cancel')),('group_id', '=', line.group_id.id)]).mapped('product_uom_qty'))
            line_value.append((0, 0, {
                    'move_id': line.id,
                    'price': line.price_unit,
                    'shipped_qty': line.product_uom_qty
                }))
        if self.is_oversea:
            old_invoice_ref = self.commercial_invoice
        else:
            old_invoice_ref = self.invoice_no
        receipt_lists = self.copy({
                    'name': 'New',
                    'line_ids': [],
                    'rl_reference': self.name,
                    'old_invoice_ref': old_invoice_ref,
                    'cost_lines': [],
                    'valuation_adjustment_lines': [],
                    'state': 'draft',
                    'confirmed_warehouse_date': False,
                    'confirmed_warehouse_by': False,
                    'warehouse_status': 'draft',
                    'validate_inventory_date': False,
                    'validate_inventory_by': False,
                    'inventory_status': 'waiting'
                })
        receipt_lists.write({'line_ids': line_value})
        return receipt_lists
    
    def revised(self):
        for line in self.line_ids:
            line.move_id.move_line_ids.unlink()
            if line.move_id.origin_rl_move_id:
                if not line.move_id.origin_rl_move_id.receipt_list_line_id:
                    origin_move = line.move_id.origin_rl_move_id
                    origin_move.product_uom_qty += line.move_id.product_uom_qty
                    line.move_id.picking_id = False
                    line.move_id._action_cancel()
                    line.move_id = origin_move
  
        self.state = "draft"
        self.warehouse_status = "draft"
        self.inventory_status = "waiting"

    def batch_add(self):
        for line in self.line_ids:
            line.batch_no = self.batch_ref
    
    def batch_remove(self):
        for line in self.line_ids:
            line.batch_no = ""

    def get_valuation_lines(self):
        self.ensure_one()
        lines = []

        for move in self.line_ids.mapped('move_id'):
            # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
            if move.product_id.cost_method not in ('fifo', 'average') or move.state == 'cancel' or not move.product_qty:
                continue
            vals = {
                'product_id': move.product_id.id,
                'move_id': move.id,
                'quantity': move.product_qty,
                'former_cost': sum(move.stock_valuation_layer_ids.mapped('value')),
                'weight': move.product_id.weight * move.product_qty,
                'volume': move.product_id.volume * move.product_qty
            }
            lines.append(vals)

        if not lines:
            target_model_descriptions = dict(self._fields['target_model']._description_selection(self.env))
            raise UserError(_("You cannot apply landed costs on the chosen %s(s). Landed costs can only be applied for products with FIFO or average costing method.", target_model_descriptions[self.target_model]))
        return lines
    
    def compute_landed_cost(self):
        AdjustementLines = self.env['stock.valuation.adjustment.lines']
        self.valuation_adjustment_lines.unlink()

        towrite_dict = {}
        for cost in self:
            rounding = cost.company_id.currency_id.rounding
            total_qty = 0.0
            total_cost = 0.0
            total_weight = 0.0
            total_volume = 0.0
            total_line = 0.0
            all_val_line_values = cost.get_valuation_lines()

            for val_line_values in all_val_line_values:
                for cost_line in cost.cost_lines:
                    val_line_values.update({'receipt_list_id': cost.id, 'cost_line_id': cost_line.id})
                    self.env['stock.valuation.adjustment.lines'].create(val_line_values)
                total_qty += val_line_values.get('quantity', 0.0)
                total_weight += val_line_values.get('weight', 0.0)
                total_volume += val_line_values.get('volume', 0.0)

                former_cost = val_line_values.get('former_cost', 0.0)
                # round this because former_cost on the valuation lines is also rounded
                total_cost += cost.company_id.currency_id.round(former_cost)

                total_line += 1

            for line in cost.cost_lines:
                value_split = 0.0
                for valuation in cost.valuation_adjustment_lines:
                    value = 0.0
                    if valuation.cost_line_id and valuation.cost_line_id.id == line.id:
                        if line.split_method == 'by_quantity' and total_qty:
                            per_unit = (line.price_unit / total_qty)
                            value = valuation.quantity * per_unit
                        elif line.split_method == 'by_weight' and total_weight:
                            per_unit = (line.price_unit / total_weight)
                            value = valuation.weight * per_unit
                        elif line.split_method == 'by_volume' and total_volume:
                            per_unit = (line.price_unit / total_volume)
                            value = valuation.volume * per_unit
                        elif line.split_method == 'equal':
                            value = (line.price_unit / total_line)
                        elif line.split_method == 'by_current_cost_price' and total_cost:
                            per_unit = (line.price_unit / total_cost)
                            value = valuation.former_cost * per_unit
                        else:
                            value = (line.price_unit / total_line)

                        if rounding:
                            value = tools.float_round(value, precision_rounding=rounding, rounding_method='UP')
                            fnc = min if line.price_unit > 0 else max
                            value = fnc(value, line.price_unit - value_split)
                            value_split += value

                        if valuation.id not in towrite_dict:
                            towrite_dict[valuation.id] = value
                        else:
                            towrite_dict[valuation.id] += value
        for key, value in towrite_dict.items():
            AdjustementLines.browse(key).write({'additional_landed_cost': value})
        return True

    def cost_validate(self):
        self.compute_landed_cost()

        for cost in self:
            cost = cost.with_company(cost.company_id)
            move = self.env['account.move']
            move_vals = {
                'journal_id': cost.account_journal_id.id,
                'date': date.today(),
                'ref': cost.name,
                'line_ids': [],
                'move_type': 'entry',
            }
            valuation_layer_ids = []
            cost_to_add_byproduct = defaultdict(lambda: 0.0)
            for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
                remaining_qty = sum(line.move_id.stock_valuation_layer_ids.mapped('remaining_qty'))
                linked_layer = line.move_id.stock_valuation_layer_ids[:1]

                # Prorate the value at what's still in stock
                cost_to_add = line.additional_landed_cost
                if not cost.company_id.currency_id.is_zero(cost_to_add):
                    valuation_layer = self.env['stock.valuation.layer'].create({
                        'value': cost_to_add,
                        'unit_cost': 0,
                        'quantity': 0,
                        'remaining_qty': 0,
                        'stock_valuation_layer_id': linked_layer.id,
                        'description': cost.name,
                        'stock_move_id': line.move_id.id,
                        'product_id': line.move_id.product_id.id,
                        'stock_landed_cost_id': cost.id,
                        'company_id': cost.company_id.id,
                    })
                    linked_layer.remaining_value += cost_to_add
                    valuation_layer_ids.append(valuation_layer.id)
                # Update the AVCO
                product = line.move_id.product_id
                if product.cost_method == 'average':
                    cost_to_add_byproduct[product] += cost_to_add
                if line.move_id:
                    line.move_id.recalculate_all_cost()
                    
                # Products with manual inventory valuation are ignored because they do not need to create journal entries.
                if product.valuation != "real_time":
                    continue
                # `remaining_qty` is negative if the move is out and delivered proudcts that were not
                # in stock.
                qty_out = 0
                if line.move_id._is_in():
                    qty_out = line.move_id.product_qty - remaining_qty
                elif line.move_id._is_out():
                    qty_out = line.move_id.product_qty
                move_vals['line_ids'] += line._create_accounting_entries(move, qty_out)
               
            move_vals['stock_valuation_layer_ids'] = [(6, None, valuation_layer_ids)]
       
            if move_vals.get("line_ids"):
                move = move.create(move_vals)

            if move:
                move._post()

        return True
    
    def check_iso_name(self, check_iso):
        for receipt in self:
            check_model = self.env["ir.actions.report"].search([('model', '=', 'receipt.list'),('report_name', '=', check_iso)], limit=1)
            if check_model:
                return check_model.iso_name
            else:
                return "-"
    
    def action_print(self):
        return self.env.ref('hdc_receipt_list.receipt_list_report_view').report_action(self)
    def action_print_shortage_overage(self):
        return self.env.ref('hdc_receipt_list.receipt_shortage_overage_report_view').report_action(self)

    def create_bills(self):
        ac_moves = []

        line_product = self.line_ids.filtered(lambda l: l.qty_to_invoice > 0)
        line_service = self.line_service_ids.filtered(lambda l: l.po_id.invoice_status != 'invoiced')

        line_ids = list(line_product) + list(line_service)

        if line_ids:
            purchase_id = line_ids[0].purchase_line_id.order_id
            ac_moves.append(purchase_id.action_create_invoice_rl(line_ids).id)
            result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
            result['domain'] = [('id', 'in', ac_moves)]
            return result
        else:
            raise ValidationError(_('ไม่มีรายการสินค้าให้เปิด Bill แล้วค่ะ'))
        
    def create_bills_tree(self):
        if not self:
            raise ValidationError(_("กรุณาเลือกเอกสาร RL อย่างน้อย 1 ใบ"))

        if any(rl.state != 'done' for rl in self):
            raise ValidationError(_("ไม่สามารถเปิดบิลได้ เนื่องจากมีเอกสารที่ไม่ได้มีสถานะ Done"))
    
        partners = self.mapped('partner_id')
        if len(partners) > 1:
            raise ValidationError(_("กรุณาตรวจสอบข้อมูล Supplier/ Vendor ที่เลือกมาไม่ตรงกันค่ะ"))
        
        currencies = self.mapped('currency_id')
        if len(currencies) > 1:
            raise ValidationError(_("ระบบตรวจสอบพบว่าสกุลเงินมีความแตกต่างกันกรุณา ตรวจสอบอีกครั้งค่ะ"))

        for rl in self:
            if any(l.qty_to_invoice <= 0 for l in rl.line_ids):
                raise ValidationError(_("ระบบตรวจสอบพบบางรายการถูกเปิดบิลแล้วกรุณา ตรวจสอบข้อมูลหน้า Generate Billing อีกครั้ง"))

        for rl in self:
            if any(l.po_id and l.po_id.invoice_status == 'invoiced' for l in rl.line_service_ids):
                raise ValidationError(_("ระบบตรวจสอบพบบางรายการถูกเปิดบิลแล้วกรุณา ตรวจสอบข้อมูลหน้า Generate Billing อีกครั้ง"))

        line_product = self.mapped('line_ids').filtered(lambda l: l.qty_to_invoice > 0)
        line_service = self.mapped('line_service_ids').filtered(lambda l: l.po_id and l.po_id.invoice_status != 'invoiced')
        line_ids = list(line_product) + list(line_service)

        if not line_ids:
            raise ValidationError(_("ไม่มีรายการสินค้าให้เปิด Bill แล้วค่ะ"))

        purchase_id = line_ids[0].purchase_line_id.order_id
        ac_moves = [purchase_id.action_create_invoice_rl(line_ids).id]

        result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_in_invoice_type')
        result['domain'] = [('id', 'in', ac_moves)]
        return result
        
class ReceiptListline(models.Model):
    _name = 'receipt.list.line'
    _description = "Receipt Lists Line"

    name = fields.Char(string="Description")
    receipt_list_id = fields.Many2one('receipt.list', string='Receipt List')
    move_id = fields.Many2one('stock.move', string='Moves', index=True)
    purchase_line_id = fields.Many2one(related="move_id.purchase_line_id", string='Purchase line')
    invoice_status = fields.Selection(related="move_id.purchase_line_id.order_id.invoice_status")
    product_id = fields.Many2one(related="move_id.product_id", string="Product")
    date = fields.Datetime(related="move_id.purchase_line_id.date_planned", string="Receipted Date")
    warehouse_id = fields.Many2one(related="move_id.warehouse_id", string="Warehouse")
    location_dest_id = fields.Many2one(related="move_id.location_dest_id", string="Location")
    reference = fields.Char(related="move_id.reference", string="Receipt No")
    group_id = fields.Many2one(related="move_id.group_id", string="PO No")
    batch_no = fields.Char(string='Batch No')
    demand_total = fields.Float(related="move_id.demand_total", string="PO Demand")
    po_remain = fields.Float(compute='_compute_po_remain', string="PO Remain")
    po_shipped_qty = fields.Float(string="PO Shipped")
    po_receipt_qty = fields.Float(string="PO Receipt QTY")
    po_receipt_done = fields.Float(string="PO Receipt Done",compute='_compute_po_receipt_done')
    po_product_uom = fields.Many2one(related='move_id.po_product_uom', string='PO UoM')
    product_uom_qty = fields.Float(related="move_id.product_uom_qty", string="Demand")
    demand = fields.Float(compute='_compute_demand', string="Remain")
    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=False)
    shipped_qty = fields.Float(string="Shipped")
    receipt_qty = fields.Float(string="Receipt QTY")
    receipt_done = fields.Float(string="Receipt Done",compute='_compute_receipt_done')
    product_uom = fields.Many2one(related='move_id.product_uom', string='UoM')
    price = fields.Float(string="Unit Price")
    subtotal = fields.Monetary(compute='_compute_amount', string="Subtotal", store=False)

    state = fields.Selection(related="move_id.state", string="Status")

    default_code = fields.Char(related="move_id.product_id.default_code", string="Internal Reference")
    barcode = fields.Char(related="move_id.product_id.barcode", string="Barcode")
    product_categ_id = fields.Many2one(related="move_id.product_id.categ_id", string="Product Category")
    product_tag_ids = fields.Many2many(related="move_id.tags_product_sale_ids", string="Product Tags")
    all_stock = fields.Float(related="move_id.product_id.qty_available", string="All Stock")
    available_stock = fields.Float(related="move_id.product_id.free_qty", string="Available Stock")
    external_barcodes = fields.One2many(related="move_id.product_id.barcode_spe_ids", string="External Barcode")
    remark = fields.Char(string="Remarks")
    hs_code = fields.Many2one(related="move_id.product_id.hs_code_id", string="HS Code")
    duty = fields.Float(related="hs_code.duty", string="Duty %")
    box = fields.Integer(related="move_id.product_id.box", string="กล่องละ")
    crate = fields.Integer(related="move_id.product_id.crate", string="ลังละ")

    net_price = fields.Monetary(compute='_compute_amount', string="Net Price", store=False)

    std_price = fields.Float(string="Std Price",related="product_id.lst_price")
    discount = fields.Char(related="move_id.purchase_line_id.multi_disc", string="Discount")
    taxes_id = fields.Many2many(related="move_id.purchase_line_id.taxes_id", string="Taxes")
    currency_id = fields.Many2one(related="move_id.purchase_line_id.currency_id", string="Currency")
    vendor_bill_id = fields.Many2one('account.move', string='Vendor Bill', copy = False) 
    vendor_bill_state = fields.Selection(related='vendor_bill_id.state',string="Vendor Bill Status")

    # Replace by invoiced Qty
    invoice_lines = fields.One2many('account.move.line', 'receipt_list_id', string="Bill Lines", readonly=True, copy=False)
    qty_invoiced = fields.Float(compute='_compute_qty_invoiced', string="Billed Qty", digits='Product Unit of Measure', store=True, index=True)
    qty_to_invoice = fields.Float(compute='_compute_qty_invoiced', string='Qty to Bill', digits='Product Unit of Measure', store=True, index=True)

    def action_remove_line(self):
        self.unlink()

    def convert_uom_factor(self, product=False, qty=0, move_po_uom=False):

        if not (product and qty and move_po_uom):
            qty = 0
            return qty

        base_map = product.product_tmpl_id.uom_map_ids.filtered(
            lambda l: l.uom_type == "base" and l.product_id.id == product.id
        )
        if not base_map:  # ตรวจว่ามี factor, uom ที่ base มั้ย
            qty = 0
            return qty
        
        base_uom = base_map[0].uom_id

        po_map = product.product_tmpl_id.uom_map_ids.filtered(
            lambda l: l.uom_id.id == move_po_uom.id and l.product_id.id == product.id
        )
        if (
            not po_map or not po_map[0].factor_base
        ):  # ตรวจว่ามี factor, uom ที่เราส่งมามั้ย
            qty = 0
            sale_line_uom = False
            return qty, sale_line_uom

        factor = po_map[0].factor_base
        product_qty_f = qty * factor

        return product_qty_f
    
    def convert_uom_factor_po(self, product=False, qty=0, move_po_uom=False):
        po_map = product.product_tmpl_id.uom_map_ids.filtered(
            lambda l: l.uom_id.id == move_po_uom.id and l.product_id.id == product.id
        )
        if (
            not po_map or not po_map[0].factor_base
        ):  # ตรวจว่ามี factor, uom ที่เราส่งมามั้ย
            qty = 0
            return qty

        factor = po_map[0].factor_base
        if factor != 0:
            product_qty_f = qty / factor
        else:
            product_qty_f = 0

        return product_qty_f
    
    @api.model
    def create(self, vals):
        record = super(ReceiptListline, self).create(vals)
        if not record.po_shipped_qty:  
            record.po_shipped_qty = record.po_remain
        return record

    # @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity','move_id.purchase_line_id.product_uom_qty', 'move_id.purchase_line_id.order_id.state')
    @api.depends('receipt_list_id.state', 'invoice_lines.move_id.state', 'invoice_lines.quantity','move_id.purchase_line_id.product_uom_qty', 'move_id.purchase_line_id.order_id.state')
    def _compute_qty_invoiced(self):
        for line in self:
            # compute qty_invoiced
            qty = 0.0
            for inv_line in line.invoice_lines:
                if inv_line.move_id.state not in ['cancel']:
                    if inv_line.move_id.move_type == 'in_invoice':
                        qty += inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.move_id.po_product_uom)
                    elif inv_line.move_id.move_type == 'in_refund':
                        qty -= inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.move_id.po_product_uom)
            line.qty_invoiced = qty

            # compute qty_to_invoice
            if line.move_id.purchase_line_id.order_id.state in ['purchase', 'done']:
                line.qty_to_invoice = line.po_receipt_done - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.onchange("po_receipt_qty")
    def _onchange_po_receipt_qty(self):
        if not self.env.context.get('from_receipt_qty'):
            self = self.with_context(from_po_receipt_qty=True)
            product_qty_f = self.po_receipt_qty
            if self.po_product_uom.id != self.product_uom.id:
                product_qty_f = self.convert_uom_factor(
                        self.product_id, self.po_receipt_qty, self.po_product_uom
                    )
            self.receipt_qty = product_qty_f

    @api.onchange("receipt_qty")
    def _onchange_receipt_qty(self):
        if self.receipt_qty and self.shipped_qty and self.receipt_qty > self.shipped_qty:
            raise UserError(_('Receipt QTY must be less than or equal to Shipped QTY.'))
        
        if not self.env.context.get('from_po_receipt_qty'):
            self = self.with_context(from_receipt_qty=True)
            product_qty_f = self.receipt_qty
            if self.po_product_uom.id != self.product_uom.id:
                product_qty_f = self.convert_uom_factor_po(
                    self.product_id, self.receipt_qty, self.po_product_uom
                )
            self.po_receipt_qty = product_qty_f

        if self.move_id:
            for line in self.move_id.move_line_ids:
                if self.move_id.location_dest_id == line.location_dest_id:
                    if self.receipt_qty == 0:
                        line.unlink()
                        return
                    line.qty_done = self.receipt_qty
                    return
                   
            prepare_move = {
                    'picking_id': self.move_id.picking_id.id,
                    'move_id': self.move_id.id,
                    'product_id': self.move_id.product_id.id,
                    'product_uom_id': self.move_id.product_uom.id,
                    'location_id': self.move_id.location_id.id,
                    'location_dest_id': self.receipt_list_id.location_id.id,
                    'qty_done': self.receipt_qty,
                }
            move_line_id = self.env['stock.move.line'].create(prepare_move)

    @api.onchange("po_shipped_qty")
    def _onchange_po_shipped_qty(self):
        if not self.env.context.get('from_shipped_qty'):
            self = self.with_context(from_po_shipped_qty=True)
            product_qty_f = self.po_shipped_qty
            if self.po_product_uom.id != self.product_uom.id:
                product_qty_f = self.convert_uom_factor(
                        self.product_id, self.po_shipped_qty, self.po_product_uom
                    )
            self.shipped_qty = product_qty_f

    @api.onchange("shipped_qty")
    def _onchange_shipped_qty(self):
        if self.shipped_qty > self.product_uom_qty:
            raise UserError(_('Shipped QTY must be less than or equal to Demand.'))
        if not self.env.context.get('from_po_shipped_qty'):
            self = self.with_context(from_shipped_qty=True)
            product_qty_f = self.shipped_qty
            if self.po_product_uom.id != self.product_uom.id:
                product_qty_f = self.convert_uom_factor_po(
                    self.product_id, self.shipped_qty, self.po_product_uom
                )
            self.po_shipped_qty = product_qty_f

    def _compute_demand(self):
        for move in self:
            move.demand = move.move_id.product_uom_qty

    def _compute_po_remain(self):
        for move in self:
            product_qty_f = move.demand
            if move.po_product_uom.id != move.product_uom.id:
                product_qty_f = move.convert_uom_factor_po(
                    move.product_id, move.demand, move.po_product_uom
                )
            move.po_remain = product_qty_f

    def _compute_receipt_done(self):
        for line in self:
            line.receipt_done = sum(line.move_id.move_line_ids.mapped('qty_done'))

    def _compute_po_receipt_done(self):
        for line in self:
            product_qty_f = line.receipt_done
            if line.po_product_uom.id != line.product_uom.id:
                product_qty_f = line.convert_uom_factor_po(
                    line.product_id, line.receipt_done, line.po_product_uom
                )
            line.po_receipt_done = product_qty_f

    @api.depends('price', 'demand', 'po_shipped_qty', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            taxes = line.taxes_id.compute_all(
                vals['price_unit'],
                vals['currency_id'],
                vals['product_qty'],
                vals['product'],
                vals['partner'])
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'net_price': taxes['total_included'],
                'subtotal': taxes['total_excluded'],
            })

    def _prepare_compute_all_values(self):
        # Hook method to returns the different argument values for the
        # compute_all method, due to the fact that discounts mechanism
        # is not implemented yet on the purchase orders.
        # This method should disappear as soon as this feature is
        # also introduced like in the sales module.
        self.ensure_one()
        return {
            'price_unit': self.price,
            'currency_id': self.currency_id,
            'product_qty': self.po_shipped_qty,
            'product': self.product_id,
            'partner': self.receipt_list_id.partner_id,
        }
    
    def write(self, vals):
        if vals.get('price'):
            self.env['purchase.rl.history'].create({
                'purchase_id': self.move_id.purchase_line_id.order_id.id,
                'receipt_list_id': self.receipt_list_id.id,
                'product_id': self.product_id.id,
                'receipt_no': self.reference,
                'po_no': self.group_id.name,
                'before_price': self.price,
                'price': vals.get('price'),
            })
        return super(ReceiptListline, self).write(vals)

    def action_show_details(self):
        """ Returns an action that will open a form view (in a popup) allowing to work on all the
        move lines of a particular move. This form view is used when "show operations" is not
        checked on the picking type.
        """
        self.ensure_one()
        self = self.move_id
        picking_type_id = self.picking_type_id or self.picking_id.picking_type_id

        # If "show suggestions" is not checked on the picking type, we have to filter out the
        # reserved move lines. We do this by displaying `move_line_nosuggest_ids`. We use
        # different views to display one field or another so that the webclient doesn't have to
        # fetch both.
        if picking_type_id.show_reserved:
            view = self.env.ref('stock.view_stock_move_operations')
        else:
            view = self.env.ref('stock.view_stock_move_nosuggest_operations')

        return {
            'name': _('Detailed Operations'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
                show_owner=self.picking_type_id.code != 'incoming',
                show_lots_m2o=self.has_tracking != 'none' and (picking_type_id.use_existing_lots or self.state == 'done' or self.origin_returned_move_id.id),  # able to create lots, whatever the value of ` use_create_lots`.
                show_lots_text=self.has_tracking != 'none' and picking_type_id.use_create_lots and not picking_type_id.use_existing_lots and self.state != 'done' and not self.origin_returned_move_id.id,
                show_source_location=self.picking_type_id.code != 'incoming',
                show_destination_location=self.picking_type_id.code != 'outgoing',
                show_package=not self.location_id.usage == 'supplier',
                show_reserved_quantity=self.state != 'done' and not self.picking_id.immediate_transfer and self.picking_type_id.code != 'incoming'
            ),
        }
    

    shortage_qty = fields.Float(string="Shortage QTY",
                            compute="_compute_shortage_overage_qty", store=True)
    overage_qty  = fields.Float(string="Overage QTY",
                                compute="_compute_shortage_overage_qty", store=True)

    @api.depends('shipped_qty', 'receipt_done', 'receipt_qty', 'receipt_list_id.state')
    def _compute_shortage_overage_qty(self):
        for move in self:
            shipped  = move.shipped_qty or 0.0
            received = move.receipt_done or 0.0
            move.shortage_qty = shipped - received if shipped > received else 0.0
            move.overage_qty = received - shipped if received > shipped else 0.0

    def update_po_ship_and_receipt(self):
        domain = [('receipt_list_id.state', '!=', 'cancel')]
        rl_line = self.env['receipt.list.line'].search(domain)

        for line in rl_line:
            if line.po_product_uom.id == line.product_uom.id:
                line = line.with_context(from_shipped_qty=True)
                line.po_shipped_qty = line.shipped_qty
                line = line.with_context(from_receipt_qty=True)
                line.po_receipt_qty = line.receipt_qty
            else:
                line = line.with_context(from_shipped_qty=True)
                po_shipped_qty = line.convert_uom_factor_po(
                    line.product_id, line.shipped_qty, line.po_product_uom
                )
                line.po_shipped_qty = po_shipped_qty
                line = line.with_context(from_receipt_qty=True)
                po_receipt_qty = line.convert_uom_factor_po(
                    line.product_id, line.receipt_qty, line.po_product_uom
                )
                line.po_receipt_qty = po_receipt_qty

    def update_qty_invoiced(self):
        domain = [('receipt_list_id.state', '!=', 'draft')]
        rl_line = self.env['receipt.list.line'].search(domain)
        for line in rl_line:
            # compute qty_invoiced
            qty = 0.0
            for inv_line in line.invoice_lines:
                if inv_line.move_id.state not in ['cancel']:
                    if inv_line.move_id.move_type == 'in_invoice':
                        qty += inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.move_id.po_product_uom)
                    elif inv_line.move_id.move_type == 'in_refund':
                        qty -= inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.move_id.po_product_uom)
            line.qty_invoiced = qty

            # compute qty_to_invoice
            if line.move_id.purchase_line_id.order_id.state in ['purchase', 'done']:
                line.qty_to_invoice = line.po_receipt_done - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

class ReceiptListlineService(models.Model):
    _name = 'receipt.list.line.service'
    _description = "Receipt Lists Line Service"


    name = fields.Char(string="Description")
    receipt_list_id = fields.Many2one('receipt.list', string='Receipt List', index=True, ondelete="cascade")
    purchase_line_id = fields.Many2one('purchase.order.line', string='Purchase line', index=True, ondelete="cascade")
    product_id = fields.Many2one(related="purchase_line_id.product_id", string="Product")
    po_id = fields.Many2one(related="purchase_line_id.order_id", string="PO No")
    demand = fields.Float(related="purchase_line_id.product_qty", string="QTY")
    price = fields.Float(related="purchase_line_id.gross_unit_price", string="Unit Price")
    subtotal = fields.Monetary(related="purchase_line_id.price_subtotal", string="Subtotal", store=True)
    currency_id = fields.Many2one(related="purchase_line_id.currency_id", string="Currency")
    invoice_lines = fields.One2many('account.move.line', 'service_list_id', string="Bill Lines", readonly=True, copy=False)




