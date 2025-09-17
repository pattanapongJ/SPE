from odoo import api, fields, models, tools, _
from collections import defaultdict
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_is_zero
from odoo.tools import float_round

class StockLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    state = fields.Selection(selection_add=[('waiting_adjustment', "Waiting Valuation Adjustment"),("done",)])
    account_journal_id = fields.Many2one(
        'account.journal', 'Account Journal', domain=[("type", "in", ('purchase', 'general'))],
        required=True, states={'done': [('readonly', True)]}, default=lambda self: self._default_account_journal_id()) 

    cal_currency_id = fields.Many2one('res.currency', string='Currency', readonly=False)
    exchange_date = fields.Date(string='Exchange Date')
    exchange_rate = fields.Float(string='Exchange Rate', readonly=False)
    
    target_type = fields.Selection(
        [('manual', 'Manual (Import/Export)'),
         ('computed','Computed Landed Cost ')], 
        string="Type",
        required=True, default='computed',
        copy=False, states={'done': [('readonly', True)]})
    
    valuation_adjustment_manual_lines = fields.One2many(
        'stock.valuation.adjustment.manual.lines', 'cost_id', 'Valuation Adjustments Manual',
        states={'draft': [('readonly', True)],'waiting_adjustment': [('readonly', False)],'done': [('readonly', True)]})
    
    target_model = fields.Selection(selection_add=[
        ('receipt_list', "Receipt List")
    ], ondelete={'receipt_list': 'set default'})

    receipt_list_ids = fields.Many2many(
        'receipt.list', string='Receipt Lists',
        copy=False, states={'done': [('readonly', True)]},)
        
    allowed_receipt_list_ids = fields.Many2many(
        'stock.picking.batch', compute='_compute_allowed_receipt_list_ids')
    
    receipts_date = fields.Datetime(string="Receipts Date", default=False, copy=False,states={'done': [('readonly', True)]}, tracking=True)

    vendor_bill_id = fields.Many2many(
        'account.move', string='Vendor Bill', copy=False, domain=[('move_type', '=', 'in_invoice')])
    
    @api.onchange('receipt_list_ids', 'picking_ids')
    def _onchange_receipts_date(self):
        for rec in self:
            print('---------------')
            rec.receipts_date = False
            if rec.receipt_list_ids:
                rec.receipts_date = rec.receipt_list_ids[0].validate_inventory_date
                rec.cal_currency_id = rec.receipt_list_ids[0].currency_id.id

            if rec.picking_ids:
                rec.receipts_date = rec.picking_ids[0].validate_date

    @api.onchange('exchange_date')
    def _onchange_exchange_date(self):
        if self.exchange_date:
            exchange_rate = self.env['res.currency.rate'].search([
                ('name', '=', self.exchange_date),
                ('currency_id', '=', self.cal_currency_id.id),
            ], limit=1).inverse_company_rate

            if exchange_rate:
                self.exchange_rate = exchange_rate
            else:
                raise ValidationError("No exchange rate found for the selected date and currency.")
            
    @api.onchange('target_model')
    def _onchange_target_model(self):
        super()._onchange_target_model()
        self.receipts_date = False
        if self.target_model != 'receipt_list':
            self.receipt_list_ids = False

    @api.depends('company_id')
    def _compute_allowed_receipt_list_ids(self):
        for cost in self:
            moves = self.env['stock.move'].search([
                ('stock_valuation_layer_ids', '!=', False),
                ('batch_id', '!=', False),
                ('company_id', '=', cost.company_id.id)
            ])
            self.allowed_receipt_list_ids = moves.batch_id
    
    def get_product_manual(self):
        AdjustementManualLines = self.env['stock.valuation.adjustment.manual.lines']
        AdjustementManualLines.search([('cost_id', 'in', self.ids)]).unlink()
        if self.cost_lines:
            for cost_line in self.cost_lines:
                if self.target_model == 'picking':
                    for picking in self.picking_ids:
                        for move in picking.move_lines:
                            vals = {
                                'cost_id': self.id,
                                'cost_line_id': cost_line.id,
                                'picking_id': picking.id,
                                'product_id': move.product_id.id,
                                'move_id': move.id,
                                'quantity': move.product_qty,
                                'former_cost': sum(move.stock_valuation_layer_ids.mapped('value')),
                            }
                            self.env['stock.valuation.adjustment.manual.lines'].create(vals)
                elif self.target_model == 'manufacturing':
                    for production in self.mrp_production_ids:
                        for move in production.move_finished_ids:
                            vals = {
                                'cost_id': self.id,
                                'cost_line_id': cost_line.id,
                                'mrp_production_id': production.id,
                                'product_id': move.product_id.id,
                                'move_id': move.id,
                                'quantity': move.product_qty,
                                'former_cost': sum(move.stock_valuation_layer_ids.mapped('value')),
                            }
                            self.env['stock.valuation.adjustment.manual.lines'].create(vals)
                elif self.target_model == 'receipt_list':
                    for receipt_list in self.receipt_list_ids:
                        for line_ids in receipt_list.line_ids:
                            vals = {
                                'cost_id': self.id,
                                'receipt_name': receipt_list.name,
                                'cost_line_id': cost_line.id,
                                'receipt_list_id': receipt_list.id,
                                'product_id': line_ids.move_id.product_id.id,
                                'move_id': line_ids.move_id.id,
                                'quantity': line_ids.move_id.product_qty,
                                'former_cost': sum(line_ids.move_id.stock_valuation_layer_ids.mapped('value')),
                            }
                            self.env['stock.valuation.adjustment.manual.lines'].create(vals)
        else:
            if self.target_model == 'picking':
                for picking in self.picking_ids:
                    for move in picking.move_lines:
                        vals = {
                            'cost_id': self.id,
                            'picking_id': picking.id,
                            'product_id': move.product_id.id,
                            'move_id': move.id,
                            'quantity': move.product_qty,
                            'former_cost': sum(move.stock_valuation_layer_ids.mapped('value')),
                        }
                        self.env['stock.valuation.adjustment.manual.lines'].create(vals)
            elif self.target_model == 'manufacturing':
                for production in self.mrp_production_ids:
                    for move in production.move_finished_ids:
                        vals = {
                            'cost_id': self.id,
                            'mrp_production_id': production.id,
                            'product_id': move.product_id.id,
                            'move_id': move.id,
                            'quantity': move.product_qty,
                            'former_cost': sum(move.stock_valuation_layer_ids.mapped('value')),
                        }
                        self.env['stock.valuation.adjustment.manual.lines'].create(vals)
            elif self.target_model == 'receipt_list':
                for receipt_list in self.receipt_list_ids:
                    for line_ids in receipt_list.line_ids:
                        print('----------------receipt_list.name', receipt_list.name)
                        vals = {
                            'cost_id': self.id,
                            'receipt_name': receipt_list.name,
                            'receipt_list_id': receipt_list.id,
                            'product_id': line_ids.move_id.product_id.id,
                            'move_id': line_ids.move_id.id,
                            'quantity': line_ids.move_id.product_qty,
                            'former_cost': sum(line_ids.move_id.stock_valuation_layer_ids.mapped('value')),
                        }
                        self.env['stock.valuation.adjustment.manual.lines'].create(vals)

    def export_adjustment_manual_lines(self):
        self.ensure_one()
        report = self.env['ir.actions.report'].search(
        [('report_name', '=', 'export_adjustment_manual_line_report_xlsx'),
        ('report_type', '=', 'xlsx')], limit=1)
        report.report_file = 'Landed Cost - Valuation Adjustments Manual -' + self.name
        return report.report_action(self)

    def wizard_import_adjustment_manual_lines(self):
        self.ensure_one()
        return {
                "name": "Import",
                "type": "ir.actions.act_window",
                "res_model": "wizard.import.adjustment.manual.line",
                "view_mode": 'form',
                'target': 'new',
                "context": {"default_cost_id": self.id,},
        }
    
    def action_confirm(self):
        if self.target_type == 'manual':
            AdjustementManualLines = self.env['stock.valuation.adjustment.manual.lines']
            value = AdjustementManualLines.search([('cost_id', 'in', self.ids)])
            if not value:
                self.get_product_manual()
        elif self.target_type == 'computed':
            AdjustementLines = self.env['stock.valuation.adjustment.lines']
            AdjustementLines.search([('cost_id', 'in', self.ids)]).unlink()
            self.compute_landed_cost()

        self.state = 'waiting_adjustment'

    def get_valuation_lines(self):
        self.ensure_one()
        lines = []

        for move in self._get_targeted_move_ids():
            # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
            if move.product_id.cost_method not in ('fifo', 'average') or move.state == 'cancel' or not move.product_qty:
                continue

            vals = {
                'receipt_name': move.receipt_list_line_id[0].receipt_list_id.name if move.receipt_list_line_id else move.picking_id.name ,
                'product_id': move.product_id.id,
                'duty': move.product_id.hs_code_id.duty,
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

    def _get_targeted_move_ids(self):
        if self.target_model == 'picking':
            return self.picking_ids.move_lines
        elif self.target_model == 'manufacturing':
            return self.mrp_production_ids.move_finished_ids
        elif self.target_model == 'receipt_list':
            move_ids = self.env['stock.move']
            for receipt_list in self.receipt_list_ids:
                for line_ids in receipt_list.line_ids:
                    move_ids += line_ids.move_id
            print('---------_get_targeted_move_ids-', move_ids)
            return move_ids
        
    def compute_landed_cost(self):
        AdjustementLines = self.env['stock.valuation.adjustment.lines']
        AdjustementLines.search([('cost_id', 'in', self.ids)]).unlink()

        towrite_dict = {}
        for cost in self.filtered(lambda cost: cost._get_targeted_move_ids()):
            print('---------cost-', cost)
            rounding = cost.currency_id.rounding
            total_qty = 0.0
            total_cost = 0.0
            total_weight = 0.0
            total_volume = 0.0
            total_line = 0.0
            all_val_line_values = cost.get_valuation_lines()
            for val_line_values in all_val_line_values:
                for cost_line in cost.cost_lines:
                    val_line_values.update({'cost_id': cost.id, 'cost_line_id': cost_line.id})
                    self.env['stock.valuation.adjustment.lines'].create(val_line_values)
                total_qty += val_line_values.get('quantity', 0.0)
                total_weight += val_line_values.get('weight', 0.0)
                total_volume += val_line_values.get('volume', 0.0)

                former_cost = val_line_values.get('former_cost', 0.0)
                # round this because former_cost on the valuation lines is also rounded
                total_cost += cost.currency_id.round(former_cost)

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

    def _check_can_validate(self):
        if any(cost.state != 'waiting_adjustment' for cost in self):
            raise UserError(_('Only draft landed costs can be validated'))
        for cost in self:
            if not cost._get_targeted_move_ids():
                target_model_descriptions = dict(self._fields['target_model']._description_selection(self.env))
                raise UserError(_('Please define %s on which those additional costs should apply.', target_model_descriptions[cost.target_model]))

    def button_validate(self):
        self._check_can_validate()
        cost_without_adjusment_lines = self.filtered(lambda c: not c.valuation_adjustment_lines)
        if cost_without_adjusment_lines:
            cost_without_adjusment_lines.compute_landed_cost()
        if not self._check_sum():
            raise UserError(_('Cost and adjustments lines do not match. You should maybe recompute the landed costs.'))

        for cost in self:
            cost = cost.with_company(cost.company_id)
            move = self.env['account.move']
            move_vals = {
                'journal_id': cost.account_journal_id.id,
                'date': cost.date,
                'ref': cost.name,
                'line_ids': [],
                'move_type': 'entry',
            }
            valuation_layer_ids = []
            cost_to_add_byproduct = defaultdict(lambda: 0.0)
            adjustment_lines = cost.valuation_adjustment_lines

            if self.target_type == 'manual':
                adjustment_lines = cost.valuation_adjustment_manual_lines
            
            for line in adjustment_lines.filtered(lambda line: line.move_id):
                remaining_qty = sum(line.move_id.stock_valuation_layer_ids.mapped('remaining_qty'))
                linked_layer = line.move_id.stock_valuation_layer_ids[:1]

                # Prorate the value at what's still in stock
                additional_landed_cost = 0
                if self.target_type == 'manual':
                    additional_landed_cost = line.landed_value + line.customs_duty_value
                elif self.target_type == 'computed':
                    additional_landed_cost = line.additional_landed_cost

                cost_to_add = (remaining_qty / line.move_id.product_qty) * additional_landed_cost
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
                        'new_date_cost': cost.receipts_date
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

            if self.target_type == 'computed':  
                # batch standard price computation avoid recompute quantity_svl at each iteration
                # products = self.env['product.product'].browse(p.id for p in cost_to_add_byproduct.keys())
                # for product in products:  # iterate on recordset to prefetch efficiently quantity_svl
                #     if not float_is_zero(product.quantity_svl, precision_rounding=product.uom_id.rounding):
                #         product.with_company(cost.company_id).sudo().with_context(disable_auto_svl=True).standard_price += cost_to_add_byproduct[product] / product.quantity_svl

                move_vals['stock_valuation_layer_ids'] = [(6, None, valuation_layer_ids)]
                # We will only create the accounting entry when there are defined lines (the lines will be those linked to products of real_time valuation category).
                cost_vals = {'state': 'done'}
                if move_vals.get("line_ids"):
                    move = move.create(move_vals)
                    cost_vals.update({'account_move_id': move.id})
                cost.write(cost_vals)
                if cost.account_move_id:
                    move._post()
                for invoice in cost.vendor_bill_id:
                    print('1---------------invoice', invoice, invoice.name)
                    if invoice and invoice.state == 'posted' and cost.company_id.anglo_saxon_accounting:
                        all_amls = invoice.line_ids | cost.account_move_id.line_ids
                        for product in cost.cost_lines.product_id:
                            accounts = product.product_tmpl_id.get_product_accounts()
                            input_account = accounts['stock_input']
                            all_amls.filtered(lambda aml: aml.account_id == input_account and not aml.reconciled).reconcile()
            elif self.target_type == 'manual':
                cost_vals = {'state': 'done'}
                cost.write(cost_vals)
        return True
    
    @api.onchange('vendor_bill_id')
    def _onchange_vendor_bill_id_update_additional_costs(self):
        if self.state == 'draft':
            self.cost_lines = False
            if self.vendor_bill_id:
                new_cost_lines = []
                for invoice in self.vendor_bill_id:
                    print('---------------invoice', invoice, invoice.name)
                    for invoice_line in invoice.invoice_line_ids:
                        product = invoice_line.product_id
                        if product and product.landed_cost_ok and invoice_line.is_landed_costs_line:
                            cost_line = self.env['stock.landed.cost.lines'].new({
                                'product_id': product.id,
                            })
                            
                            cost_line.onchange_product_id()
                            cost_line.price_unit = invoice_line.price_total

                            new_cost_lines.append((0, 0, {
                                'product_id': cost_line.product_id.id,
                                'name': cost_line.name,
                                'account_id': cost_line.account_id.id,
                                'price_unit': cost_line.price_unit,
                                'split_method': cost_line.split_method,
                            }))
                self.cost_lines = new_cost_lines

class AdjustmentManualLines(models.Model):
    _name = 'stock.valuation.adjustment.manual.lines'
    _description = 'Valuation Adjustment Manual Lines'

    name = fields.Char(
        'Description', compute='_compute_name', store=True)
    cost_id = fields.Many2one(
        'stock.landed.cost', 'Landed Cost',
        ondelete='cascade', required=True)
    cost_line_id = fields.Many2one(
        'stock.landed.cost.lines', 'Cost Line', readonly=True)
    picking_id = fields.Many2one('stock.picking', string='Transfers')
    mrp_production_id = fields.Many2one('mrp.production', string='Manufacturing order',)
    receipt_list_id = fields.Many2one('stock.picking.batch', string='Receipt lists')
    move_id = fields.Many2one('stock.move', 'Stock Move', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    hs_code_id = fields.Many2one(related='product_id.hs_code_id', string="HS Code")
    quantity = fields.Float(
        'Quantity', default=1.0,
        digits=0, required=True)
    former_cost = fields.Monetary('Original Value')
    customs_duty_unit = fields.Monetary('Customs Duty / Unit')
    customs_duty_value = fields.Monetary('Customs Duty Value',compute='_compute_final_cost')
    landed_value = fields.Monetary('Additional Landed Cost')
    final_cost = fields.Monetary('New Value', compute='_compute_final_cost',store=True)
    currency_id = fields.Many2one('res.currency', related='cost_id.company_id.currency_id')
    item_code = fields.Char(related='product_id.default_code', string="Item")
    free_product = fields.Boolean(string="Free Product")
    no_cal_landed_cost = fields.Boolean(string="No Calculate Landed")
    receipt_name = fields.Char(string="Receipt/RL")
    product_uom = fields.Many2one('uom.uom', related='move_id.product_uom', string="Unit")
    price_unit = fields.Float(related='move_id.price_unit', string="Unit Price")
    amount_price = fields.Float(string="Amount")
    discount = fields.Float(string="Discount")
    rate_usd = fields.Float(string="Rate USD", digits=(16,4))
    price_item = fields.Float(string="ราคาของ(บาท)", digits=(16,2))
    free_item = fields.Float(string="ของฟรี", digits=(16,2))
    amount_item = fields.Float(string="ราคาขสินค้าทั้งสิ้น", digits=(16,2))
    duty = fields.Float(string="Duty%")
    duty_avg = fields.Float(string="ค่าอากร(เฉลี่ย)", digits=(16,2))
    duty_avg2 = fields.Float(string="ค่าอากร(เฉลี่ย)2", digits=(16,2))
    duty_avg_total = fields.Float(string="ตัวเฉลี่ยอากร")
    sh_avg = fields.Float(string="เฉลี่ย SH")
    do_avg = fields.Float(string="เฉลี่ย DO")
    ins_avg = fields.Float(string="เฉลี่ย INS")
    total_duty_sh = fields.Float(string="รวมอากร +SH")
    
    @api.depends('product_id.code', 'product_id.name')
    def _compute_name(self):
        for line in self:
            line.name = (line.product_id.code or line.product_id.name or '')

    @api.depends('former_cost', 'landed_value','customs_duty_unit','customs_duty_value')
    def _compute_final_cost(self):
        for line in self:
            line.customs_duty_value = line.customs_duty_unit * line.quantity
            line.final_cost = line.former_cost + line.customs_duty_value + line.landed_value

class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'
    _description = 'Valuation Adjustment Lines'

    item_code = fields.Char(related='product_id.default_code', string="Item")
    free_product = fields.Boolean(string="Free Product")
    no_cal_landed_cost = fields.Boolean(string="No Calculate Landed")
    receipt_name = fields.Char(string="Receipt/RL")
    product_uom = fields.Many2one('uom.uom', related='move_id.product_uom', string="Unit")
    price_unit = fields.Float(related='move_id.price_unit', string="Unit Price")
    amount_price = fields.Float(string="Amount", compute='_compute_amount')
    discount = fields.Float(string="Discount", compute='_compute_amount')
    rate_usd = fields.Float(compute='_compute_rate_usd', string="Rate USD", digits=(16,4))
    price_item = fields.Float(compute='_compute_rate_usd', string="ราคาของ(บาท)", digits=(16,2))
    free_item = fields.Float(compute='_compute_rate_usd', string="ของฟรี", digits=(16,2))
    amount_item = fields.Float(compute='_compute_rate_usd', string="ราคาขสินค้าทั้งสิ้น", digits=(16,2))
    duty = fields.Float(string="Duty%")
    duty_avg = fields.Float(compute='_compute_rate_usd', string="ค่าอากร(เฉลี่ย)", digits=(16,2))
    duty_avg2 = fields.Float(compute='_compute_rate_usd', string="ค่าอากร(เฉลี่ย)2", digits=(16,2))
    duty_avg_total = fields.Float(compute='_compute_rate_usd', string="ตัวเฉลี่ยอากร")
    sh_avg = fields.Float(string="เฉลี่ย SH")
    do_avg = fields.Float(string="เฉลี่ย DO")
    ins_avg = fields.Float(string="เฉลี่ย INS")
    total_duty_sh = fields.Float(string="รวมอากร +SH")

    def _compute_amount(self):
        for rec in self:
            if rec.free_product:
                rec.discount = rec.quantity * rec.price_unit
                rec.amount_price = 0
            else:
                rec.amount_price = rec.quantity * rec.price_unit
                rec.discount = 0

    def _compute_rate_usd(self):
        for rec in self:
            rate_usd = 1
            rec.duty_avg_total = 0
            if rec.cost_id:
                if rec.cost_id.cal_currency_id.name == 'USD':
                    rate_usd =  float_round(rec.cost_id.exchange_rate, precision_digits=4, rounding_method='HALF-UP')
                    rec.rate_usd = rate_usd
                else:
                    rec.rate_usd = 0
            else:
                rec.rate_usd = 0
            if rec.free_product:
                free_item = float_round((rate_usd * rec.discount), precision_digits=2, rounding_method='HALF-UP')
                rec.duty_avg_total = free_item
                rec.free_item = free_item
                rec.duty_avg2 = float_round(((free_item * rec.duty) /100), precision_digits=2, rounding_method='HALF-UP')
                rec.duty_avg = 0
                rec.price_item = 0
            else:
                price_item = float_round((rate_usd * rec.amount_price), precision_digits=2, rounding_method='HALF-UP')
                rec.price_item = price_item
                rec.duty_avg = float_round(((price_item * rec.duty) /100), precision_digits=2, rounding_method='HALF-UP')
                rec.duty_avg2 = 0
                rec.free_item = 0
            rec.amount_item = rec.price_item + rec.free_item