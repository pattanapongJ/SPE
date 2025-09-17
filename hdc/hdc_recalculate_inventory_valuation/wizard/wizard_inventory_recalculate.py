# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date,datetime
from dateutil.relativedelta import relativedelta

class WizardInventoryRecalculate(models.TransientModel):
    _name = 'wizard.inventory.recalculate'
    _description = "Wizard to recalculate inventory valuation"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self._default_company_id(),domain=lambda self: self._get_domain_company_id(),index = True,
    )
    start_date = fields.Date(string = 'Start Date', required=True)
    target_type = fields.Selection([
        ('all', 'ALL'),
        ('categ', 'Product Category'),
        ('product', 'Product'),
    ], string="Recalculate Target",default='all')
    categ_id = fields.Many2one("product.category", "Product Category",domain="[('property_cost_method','=','average'),('property_valuation','=','manual_periodic')]")
    product_id = fields.Many2one('product.product', string='Product',domain="[('type', '=', 'product'),('categ_id.property_cost_method','=','average'),('categ_id.property_valuation','=','manual_periodic')]")
    
    @api.model
    def _default_company_id(self):
        return self.env.company
    
    @api.model
    def _get_domain_company_id(self):
        selected_companies = self.env.context.get('allowed_company_ids', [])
        domain_inter_company_id = [("id", "in", selected_companies)]
        return domain_inter_company_id
    
    @api.onchange('start_date')
    def _start_date_onchange(self):
        if self.env['ir.config_parameter'].sudo().get_param('hdc_recalculate_inventory_valuation.use_inventory_valuation_month'):
            recal_months = self.env['ir.config_parameter'].sudo().get_param('hdc_recalculate_inventory_valuation.inventory_valuation_month')
            date_today = date.today()
            minimum_start_date = date_today - relativedelta(months=int(recal_months))
            if self.start_date:
                if self.start_date < minimum_start_date:
                    self.start_date = False
                    raise UserError(_("Inventory Recalculate more than %s month") % recal_months)
        if self.start_date and self.start_date > date.today():
            self.start_date = False
            raise UserError(_("Please select a date prior to the current day."))
    
    def set_inventory_valuation_recal(self,val_id,accumulate_amount,balance_qty,avg_new,recal_order):
        if val_id.quantity > 0:
            unit_price = val_id.unit_cost
        else:
            unit_price = avg_new
            val_id.unit_cost = avg_new
            val_id.value = val_id.quantity * avg_new

        new_accumulate_amount = (unit_price * val_id.quantity) + accumulate_amount
        new_balance_qty = balance_qty + val_id.quantity  
        if new_balance_qty == 0:
            new_avg_new = 0
        else:
            new_avg_new = new_accumulate_amount/new_balance_qty
        val_id.accumulate_amount = new_accumulate_amount
        val_id.balance_qty = new_balance_qty
        val_id.avg_new = new_avg_new
        val_id.recalculate_date = date.today()
        val_id.recalculate_by = self.env.user.id
        val_id.recal_order = recal_order + 1
        
    def action_recalculate(self):
        start_time = datetime.now()
        if self.env['ir.config_parameter'].sudo().get_param('hdc_recalculate_inventory_valuation.use_inventory_valuation_month'):
            recal_months = self.env['ir.config_parameter'].sudo().get_param('hdc_recalculate_inventory_valuation.inventory_valuation_month')
            date_today = date.today()
            minimum_start_date = date_today - relativedelta(months=int(recal_months))
            if self.start_date:
                if self.start_date < minimum_start_date:
                    raise UserError(_("Inventory Recalculate more than %s month") % recal_months)
                
        search_domain = [('company_id', '=', self.company_id.id),('product_id.type', '=', 'product'),('product_id.categ_id.property_cost_method','=','average'),('product_id.categ_id.property_valuation','=','manual_periodic')]
        if self.start_date:
            search_domain.append(('create_date', '>=', self.start_date))
        if self.target_type == 'categ' and self.categ_id:
            search_domain.append(('categ_id', '=', self.categ_id.id))
        if self.target_type == 'product' and self.product_id:
            search_domain.append(('product_id', '=', self.product_id.id))

        valuations_list = self.env['stock.valuation.layer'].search(search_domain,order = "product_id asc,date_only asc, id asc")
        valuations_list_sort = sorted(valuations_list, key=lambda r: (r.product_id, r.date_only, r.quantity < 0, r.id))

        valuations_list = self.env['stock.valuation.layer'].search(search_domain,order = 'create_date asc')
        product_id = False
        accumulate_amount = 0
        balance_qty = 0
        avg_new = 0
        recal_order = 0
        product_count = 0
        
        for stock_val in valuations_list_sort:
            product_id_old = product_id

            if product_id_old == stock_val.product_id.id:
                self.set_inventory_valuation_recal(stock_val,accumulate_amount,balance_qty,avg_new,recal_order)
                accumulate_amount = stock_val.accumulate_amount
                balance_qty = stock_val.balance_qty
                avg_new = stock_val.avg_new
                recal_order = stock_val.recal_order
            else:
                # set initail each product
                product_count = product_count + 1
                product_id = stock_val.product_id.id
                accumulate_amount = 0
                balance_qty = 0
                avg_new = 0
                recal_order = 0
                valuations_id_before = self.env['stock.valuation.layer'].search([('create_date', '<', self.start_date),('product_id', '=', self.product_id.id)],order = 'create_date desc')
                if valuations_id_before:
                    accumulate_amount = valuations_id_before.accumulate_amount
                    balance_qty = valuations_id_before.balance_qty
                    avg_new = valuations_id_before.avg_new
                    recal_order = valuations_id_before.recal_order
                self.set_inventory_valuation_recal(stock_val,accumulate_amount,balance_qty,avg_new,recal_order)
                accumulate_amount = stock_val.accumulate_amount
                balance_qty = stock_val.balance_qty
                avg_new = stock_val.avg_new
                recal_order = stock_val.recal_order

        manual_log_values = {
            'recalculate_date': datetime.now(), 
            'recalculate_by':self.env.user.id,
            'total_record': len(valuations_list_sort),
            'total_product': product_count,
            'company_id': self.company_id.id,
            'start_date': self.start_date, 
            'target_type': self.target_type,
            'categ_id':self.categ_id.id,
            'product_id': self.product_id.id, 
            }

        manual_recal_log = self.env['recalculate.inventory.valuation.manual.log'].create(manual_log_values)


    def scheduled_actions_recalculate(self,company_id=False,months=False):
        if company_id:
            search_domain = [('company_id', '=', company_id),('product_id.type', '=', 'product'),('product_id.categ_id.property_cost_method','=','average'),('product_id.categ_id.property_valuation','=','manual_periodic')]
            if months:
                date_today = date.today()
                minimum_start_date = date_today - relativedelta(months=int(months))
                search_domain.append(('create_date', '>=', minimum_start_date))
            valuations_list = self.env['stock.valuation.layer'].search(search_domain,order = "product_id asc,date_only asc, id asc")
            valuations_list_sort = sorted(valuations_list, key=lambda r: (r.product_id, r.date_only, r.quantity < 0, r.id))
            product_id = False
            accumulate_amount = 0
            balance_qty = 0
            avg_new = 0
            recal_order = 0
            product_count = 0

            valuations_list = self.env['stock.valuation.layer'].search(search_domain,order = 'create_date asc')

            for stock_val in valuations_list_sort:
                product_id_old = product_id

                if product_id_old == stock_val.product_id.id:
                    self.set_inventory_valuation_recal(stock_val,accumulate_amount,balance_qty,avg_new,recal_order)
                    accumulate_amount = stock_val.accumulate_amount
                    balance_qty = stock_val.balance_qty
                    avg_new = stock_val.avg_new
                    recal_order = stock_val.recal_order
                else:
                    # set initail each product
                    product_count = product_count + 1
                    product_id = stock_val.product_id.id
                    accumulate_amount = 0
                    balance_qty = 0
                    avg_new = 0
                    recal_order = 0
                    valuations_id_before = self.env['stock.valuation.layer'].search([('create_date', '<', self.start_date),('product_id', '=', self.product_id.id)],order = 'create_date desc')
                    if valuations_id_before:
                        accumulate_amount = valuations_id_before.accumulate_amount
                        balance_qty = valuations_id_before.balance_qty
                        avg_new = valuations_id_before.avg_new
                        recal_order = valuations_id_before.recal_order
                    self.set_inventory_valuation_recal(stock_val,accumulate_amount,balance_qty,avg_new,recal_order)
                    accumulate_amount = stock_val.accumulate_amount
                    balance_qty = stock_val.balance_qty
                    avg_new = stock_val.avg_new
                    recal_order = stock_val.recal_order

            scheduled_log_values = {
                'recalculate_date': datetime.now(), 
                'total_record': len(valuations_list_sort),
                'total_product': product_count,
                'range_month': months,
                'company_id': company_id,
                }

            scheduled_recal_log = self.env['recalculate.inventory.valuation.scheduled.log'].create(scheduled_log_values)
